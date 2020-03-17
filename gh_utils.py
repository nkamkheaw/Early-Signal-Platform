import json
import logging
import requests
from typing import Any, Dict, List, Optional

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


def post_pull_request_review(base_url: str, pul_number: int, body: str, path: str, position: int, comment_body: str) -> None:
    """Post a request change on the PR for the most recent commit.
    Note: commit_id is not specified means the review will refers to the most recent commit.
    """
    check_suite_url = f"{base_url}/pulls/{pul_number}/reviews"
    payload = {"event": "REQUEST_CHANGES",
               "body": body,
               "comments": [dict(path=path, position=position, body=comment_body)]}

    make_github_rest_api_call(url=check_suite_url, method='POST', params=payload)


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
