import json
import logging
import threading
from typing import Any, Dict, Tuple

import requests

from objectify_json import ObjectifyJSON
from time import sleep

from constances import validations
from gh_oauth_token import retrieve_token
from bot_config import API_BASE_URL

log = logging.getLogger(__name__)


def make_github_rest_api_call(url: str = None, api_path: str = None, method: str = "GET", params: Dict[str, Any] = None):
    """Send API call to Github using a personal token.

Use this function to make API calls to the GitHub REST api

For example:

`GET` the current user
---
```py
me = make_github_rest_api_call("login")
```

`POST` to create a comment on a PR
---
```py
new_comment = make_github_rest_api_call(
    "repos/my_org/my_repo/issues/31/comments",
    "POST", {
        "body": "Hello there, thanks for creating a new Pull Request!"
    }
)
```
    """

    token = retrieve_token()

    # Required headers.
    headers = {"Accept": "application/vnd.github.antiope-preview+json",
               "Content-Type": "application/json",
               "Authorization": f"Bearer {token}"
               }

    # API url
    if not url:
        url = f"{API_BASE_URL}/{api_path}"

    log.info(
        f"sending {method.upper()} request to {url} w/ data {json.dumps(params)}")
    try:
        if method.upper() == "POST":
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(params),
            )
        elif method.upper() == "GET":
            response = requests.get(
                url,
                headers=headers,
            )
        else:
            raise Exception("Invalid Request Method.")
    except:
        log.exception("Could not make a successful API call to GitHub.")


class CheckSuite:
    def __init__(self, webhook: ObjectifyJSON):
        self.webhook = webhook

        # Note: in the real implementation these threads will be done through spawning jobs through task API.
        start_check_runs_thread = threading.Thread(target=self.start_check_runs())
        start_check_runs_thread.start()

    def start_check_runs(self):
        for test in validations:
            create_check_run_thread = threading.Thread(target=self.create_check_run, args=(test["name"], ))
            create_check_run_thread.start()
            sleep(1)  # simulate spawning job delay

    def create_check_run(self, name: str) -> None:
        CheckRun(self.webhook, name)


class CheckRun:
    def __init__(self, webhook: ObjectifyJSON, name: str):
        self.name: str = name

        self.repo_full_name: str = str(webhook.repository.full_name)
        self.check_suite_id: int = int(str(webhook.check_suite.id))
        self.check_suite_url: str = str(webhook.repository.url) + "/check-runs"
        self.head_branch: str = str(webhook.check_suite.head_branch)
        self.head_sha: str = str(webhook.check_suite.head_sha)
        self.git_url: str = str(webhook.repository.git_url)

        log.info(f"Running tests for {self.repo_full_name} branch {self.head_branch} ({self.head_sha})")

        self.post_check_run(check_status="in_progress")
        self.process_check_run()

    def post_check_run(self,
                       check_status: str,
                       check_conclusion: str = None,
                       output_title: str = None,
                       output_summary: str = None) -> None:

        payload = {
            "name": self.name,
            "head_sha": self.head_sha,
            "status": check_status,
        }

        if check_conclusion:
            payload['conclusion'] = check_conclusion

        if output_title and output_summary:
            payload['output'] = dict(title=output_title, summary=output_summary)

        make_github_rest_api_call(url=self.check_suite_url, method='POST', params=payload)

    def get_process_time(self) -> int:
        for test in validations:
            if self.name == test["name"]:
                return test["estimate_time"]

        log.warning(f"Can't find the test {self.name}'s estimate time.")
        return 10

    def get_mock_test_result(self) -> Tuple[str, str]:
        return "completed", "success"

    def process_check_run(self) -> None:
        sleep(self.get_process_time())
        status, conclusion = self.get_mock_test_result()
        self.post_check_run(check_status=status, check_conclusion=conclusion)
