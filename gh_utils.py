import json
import logging
import threading
from typing import Any, Dict, Tuple, Optional, List

import requests

from objectify_json import ObjectifyJSON
from time import sleep

from constances import (
    APP_NAME,
    CHECK_RUN_CONCLUSION_FAILURE,
    CHECK_RUN_CONCLUSION_SUCCESS,
    CHECK_RUN_CONCLUSION_NEUTRAL,
    CHECK_RUN_STATUS_COMPLETED,
    CHECK_RUN_STATUS_IN_PROGRESS,
    validations,
)
from gh_oauth_token import retrieve_token
from bot_config import API_BASE_URL

log = logging.getLogger(__name__)


def make_github_rest_api_call(url: str = None, api_path: str = None, method: str = "GET",
                              params: Dict[str, Any] = None) -> requests.Response:
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
        return response
    except Exception as e:
        log.exception(f"Could not make a successful API call to GitHub: {e}")


def post_check_run_result(name: str,
                          head_sha: str,
                          check_status: str,
                          base_url: str,
                          check_conclusion: str = None,
                          output_title: str = None,
                          output_summary: str = None) -> None:
    check_suite_url = f"{base_url}/check-runs"
    payload = {
        "name": name,
        "head_sha": head_sha,
        "status": check_status,
    }

    if check_conclusion:
        payload['conclusion'] = check_conclusion

    if output_title and output_summary:
        payload['output'] = dict(title=output_title, summary=output_summary)

    make_github_rest_api_call(url=check_suite_url, method='POST', params=payload)


class ProcessCheckSuite:
    def __init__(self, webhook: ObjectifyJSON):
        self.webhook = webhook

        # test variables
        self.conclusion = False  # failed
        # self.conclusion = True  # success

        # Note: in the real implementation these threads will be done through spawning jobs through task API.
        start_check_runs_thread = threading.Thread(target=self.start_check_runs())
        start_check_runs_thread.start()

    def start_check_runs(self):
        for test in validations:
            create_check_run_thread = threading.Thread(target=self.create_check_run, args=(test["name"], self.conclusion,))
            create_check_run_thread.start()
            sleep(1)  # simulate spawning job delay
            self.conclusion ^= True

    def create_check_run(self, name: str, conclusion: bool) -> None:
        ProcessCheckRun(self.webhook, name, conclusion)


class ProcessCheckRun:
    def __init__(self, webhook: ObjectifyJSON, name: str, conclusion: bool):
        self.name: str = name

        self.repo_full_name: str = str(webhook.repository.full_name)
        self.check_suite_id: int = int(str(webhook.check_suite.id))
        self.base_url: str = str(webhook.repository.url)
        self.head_branch: str = str(webhook.check_suite.head_branch)
        self.head_sha: str = str(webhook.check_suite.head_sha)
        self.git_url: str = str(webhook.repository.git_url)

        # test variable
        self.conclusion = conclusion

        log.info(f"Running tests for {self.repo_full_name} branch {self.head_branch} ({self.head_sha})")

        post_check_run_result(name=self.name,
                              head_sha=self.head_sha,
                              base_url=self.base_url,
                              check_status=CHECK_RUN_STATUS_IN_PROGRESS,
                              )
        self.process_check_run()

    def get_process_time(self) -> int:
        for test in validations:
            if self.name == test["name"]:
                return test["estimate_time"]

        log.warning(f"Can't find the test {self.name}'s estimate time.")
        return 10

    def get_mock_test_result(self) -> Tuple[str, str]:
        conclusion = CHECK_RUN_CONCLUSION_SUCCESS if self.conclusion else CHECK_RUN_CONCLUSION_FAILURE
        return CHECK_RUN_STATUS_COMPLETED, conclusion

    def process_check_run(self) -> None:
        # sleep(self.get_process_time())  # imitate the delay each test would take before getting the result is back.
        status, conclusion = self.get_mock_test_result()
        post_check_run_result(name=self.name,
                              head_sha=self.head_sha,
                              base_url=self.base_url,
                              check_status=status,
                              check_conclusion=conclusion,
                              )


def get_latest_sha(base_url: str, pr_id: int) -> Optional[str]:
    """Get the SHA of the last commit of the PR with the given ID."""
    url = f"{base_url}/pulls/{pr_id}"
    response = make_github_rest_api_call(url)
    try:
        return response.json()["head"]["sha"]
    except Exception as e:
        log.error(f"Failed to get head SHA: {e}")
        return None


def get_check_runs(base_url: str, head_sha: str) -> List[Dict[str, Any]]:
    """Get a list of check runs of the given head SHA."""
    check_runs_url = f"{base_url}/commits/{head_sha}/check-runs"
    response = make_github_rest_api_call(check_runs_url)

    try:
        return response.json()["check_runs"]
    except Exception as e:
        log.error(f"Failed to get check runs: {e}")
        return []


def neutralize_failed_check_runs(base_url: str, head_sha: str) -> None:
    """Go through the check runs of the given head SHA and replace the conclusion from 'failure' to 'neutral'."""
    for run in get_check_runs(base_url, head_sha):
        if run["app"]["name"] == APP_NAME and run["conclusion"] == CHECK_RUN_CONCLUSION_FAILURE:
            log.info(f"Neutralizing the {run['name']}.")
            post_check_run_result(name=run["name"],
                                  head_sha=head_sha,
                                  base_url=base_url,
                                  check_status=CHECK_RUN_STATUS_COMPLETED,
                                  check_conclusion=CHECK_RUN_CONCLUSION_NEUTRAL,
                                  )


def neutralize_latest_check_suite(webhook):
    """Neutralize all of the failed check runs of the last commit in the PR that the comment is from."""
    base_url = webhook.issue.repository_url
    head_sha = get_latest_sha(base_url, webhook.issue.number)

    if not head_sha:
        log.error("Abort neutralizing the latest check suite.")
        return

    log.info(f"Neutralizing {webhook.repository.full_name} PR {webhook.issue.number} head sha {head_sha}")
    neutralize_failed_check_runs(base_url, head_sha)
