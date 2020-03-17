import logging
import threading

from objectify_json import ObjectifyJSON
from time import sleep
from typing import Any, Dict, Tuple, Optional, List

from constances import (
    APP_NAME,
    CHECK_RUN_STATUS_COMPLETED,
    CHECK_RUN_STATUS_IN_PROGRESS,
    CHECK_STATUS_FAILURE,
    CHECK_STATUS_RUNNING,
    CHECK_STATUS_NEUTRAL,
    CHECK_STATUS_SUCCESS,
    CHECK_RUN_TITLE,
    ESP_OVERRIDE_STRING,
    check_status_lookup,
    validations,
)
from gh_utils import get_check_runs, post_check_run_result, get_latest_sha, post_pull_request_review

log = logging.getLogger(__name__)


class ProcessCheckRun:
    def __init__(self, webhook: ObjectifyJSON):
        self.webhook = webhook

        # Test variables.
        self._result = False  # failed
        # self._result = True  # success

        self.base_url: str = str(webhook.repository.url)
        self.head_sha: str = str(webhook.pull_request.head.sha) if webhook.pull_request else str(webhook.check_suite.head_sha)

        self.checks: List[Check] = []

        self.link = "https://crt.prod.linkedin.com/#/testing/executions/e49a13da-126a-4726-a045-09dbdbb68a2f/execution"

    def generate_output_summary(self) -> str:
        """Aggregate all the test results from checks."""
        summary = ""

        for check in self.checks:
            summary += check.get_check_result() + "\n"

        summary += f"\n***\n#### [Check execution URL]({self.link})"

        return summary

    def start(self) -> None:
        # Note: in the real implementation these threads will be done through spawning jobs through task API.
        start_check_runs_thread = threading.Thread(target=self.create_checks())
        start_check_runs_thread.start()

    def create_checks(self) -> None:
        """Create all check objects, then start processing them."""
        for test in validations:
            check = Check(test["name"], self.webhook, self._result)
            self.checks.append(check)

            # Simulate some tests success, some failed.
            # self._result ^= True

        self.process_checks()

    def process_checks(self) -> None:
        """Kick start every check and update the result as they're available.
        Then update the check run conclusion when every test is done.
        """
        threads = set()

        for check in self.checks:
            thread = threading.Thread(target=check.process_check)
            threads.add(thread)

        # Start every check.
        for thread in threads:
            thread.start()

        # Update the results whenever any test is done.
        while threads:
            sleep(1)
            removing = set()
            for thread in threads:
                if not thread.is_alive():
                    self.update_check_results()
                    removing.add(thread)
            threads -= removing

    def determine_check_run_progress(self) -> Tuple[str, str]:
        """Determine the progress of the check run.
        When all of the checks are done, the check run status will be completed with conclusion based on the check results.
        Otherwise, there's no conclusion yet and the status will be CHECK_RUN_STATUS_IN_PROGRESS.
        """
        check_size = len(self.checks)
        conclusion = CHECK_STATUS_SUCCESS
        status = CHECK_RUN_STATUS_COMPLETED

        for check in self.checks:
            if check.status != CHECK_STATUS_RUNNING:
                check_size -= 1

            # Any of the check is failed, the entire check run will be considered as failed.
            if check.status == CHECK_STATUS_FAILURE:
                conclusion = CHECK_STATUS_FAILURE

        # if there's one check is not done yet, the entire check run is still in progress.
        if check_size:
            status = CHECK_RUN_STATUS_IN_PROGRESS
            conclusion = ""

        return conclusion, status

    def update_check_results(self) -> None:
        """Update date the entire check run result page."""
        conclusion, status = self.determine_check_run_progress()
        post_check_run_result(name=APP_NAME,
                              head_sha=self.head_sha,
                              base_url=self.base_url,
                              check_status=status,
                              check_conclusion=conclusion,
                              output_title=CHECK_RUN_TITLE,
                              output_summary=self.generate_output_summary(),
                              )


class Check:
    def __init__(self, name: str, webhook: ObjectifyJSON, _result: bool):
        self.name = name

        self.base_url: str = str(webhook.repository.url)

        self.check_suite_re_request = False
        self.pull_number: int = int(str(webhook.pull_request.number))

        # check run can be triggered by either pull request [opened, updated] or check suite [rerequested]
        if not webhook.pull_request:
            self.check_suite_re_request = True
            self.pull_number = int(str(webhook.check_suite.pull_requests[0].number))  # same PR has the same number

        self.status = CHECK_STATUS_RUNNING
        self.link = ""
        self.head_sha = webhook

        # test variable
        self._result = _result

    def get_process_time(self) -> int:
        for test in validations:
            if self.name == test["name"]:
                return test["estimate_time"]

        log.warning(f"Can't find the test {self.name}'s estimate time.")
        return 5

    def get_link(self) -> str:
        for test in validations:
            if self.name == test["name"]:
                return test["good_link"] if self._result else test["bad_link"]

        log.warning(f"Can't find the test {self.name}'s estimate time.")
        return ""

    def process_check(self) -> None:
        log.info(f"Starting {self.name}")
        sleep(self.get_process_time())  # imitate the delay each test would take before getting the result is back.
        self.status = CHECK_STATUS_SUCCESS
        self.link = self.get_link()

        if not self._result:
            self.status = CHECK_STATUS_FAILURE
            # post a request change when the check fails
            post_pull_request_review(self.base_url,
                                     self.pull_number,
                                     body=f"{self.name} detects some error(s).",
                                     path="README.md", position=1,
                                     comment_body="This needs to be fixed.",
                                     )

        log.info(f"Finish {self.name}")

    def get_check_result(self) -> str:
        link = f"[See more details]({self.link})\n" if self.link else ""
        return f"### {self.name}\n" \
               f"{check_status_lookup[self.status]['icon']} The test is {check_status_lookup[self.status]['text']}.\n" \
               f"{link}"


def neutralize_failed_check_runs(base_url: str, head_sha: str) -> None:
    """Go through the check runs of the given head SHA and replace the conclusion from 'failure' to 'neutral'."""
    for run in get_check_runs(base_url, head_sha):
        if run["app"]["name"] == APP_NAME:
            log.info(f"Neutralizing the check run.")
            post_check_run_result(name=run["name"],
                                  head_sha=head_sha,
                                  base_url=base_url,
                                  check_status=CHECK_RUN_STATUS_COMPLETED,
                                  check_conclusion=CHECK_STATUS_NEUTRAL,
                                  output_title=f"{CHECK_RUN_TITLE} - Overrided",
                                  output_summary=run["output"]["summary"],
                                  )


def comment_contains_override_string(comment: str) -> bool:
    """Determine whether the comment contains the override string."""
    for line in comment.splitlines():
        if line == ESP_OVERRIDE_STRING:
            return True

    return False


def neutralize_latest_check_suite(webhook):
    """Neutralize all of the failed check runs of the last commit in the PR that the comment is from."""
    base_url = webhook.issue.repository_url
    head_sha = get_latest_sha(base_url, webhook.issue.number)

    if not comment_contains_override_string(str(webhook.comment.body)):
        log.debug(f"Ignore the comment.")
        return

    log.info(f"ESP override string detected.")

    if not head_sha:
        log.error("Abort neutralizing the latest check suite.")
        return

    log.info(f"Neutralizing {webhook.repository.full_name} PR {webhook.issue.number} head sha {head_sha}")
    neutralize_failed_check_runs(base_url, head_sha)
