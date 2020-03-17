from typing import Any, Dict, List

APP_NAME: str = "Early Signal Platform"

ESP_OVERRIDE_STRING: str = "ESPOVERRIDE"

CHECK_RUN_TITLE: str = "Test Results"

CHECK_RUN_STATUS_IN_PROGRESS: str = "in_progress"
CHECK_RUN_STATUS_COMPLETED: str = "completed"

CHECK_STATUS_RUNNING: str = "in_progress"           # Run status: in_progress
CHECK_STATUS_SUCCESS: str = "success"               # Run status: completed, run conclusion: success
CHECK_STATUS_FAILURE: str = "failure"               # Run status: completed, run conclusion: failure
CHECK_STATUS_NEUTRAL: str = "neutral"               # Run status: completed, run conclusion: neutral

check_status_lookup: Dict[str, Dict[str, str]] = {
    CHECK_STATUS_RUNNING: {"icon": ":clock1030:",
                           "text": "in progress",
                           },
    CHECK_STATUS_SUCCESS: {"icon": ":white_check_mark:",
                           "text": "success"
                           },
    CHECK_STATUS_FAILURE: {"icon": ":boom:",
                           "text": "failed",
                           },
    CHECK_STATUS_NEUTRAL: {"icon": ":thought_balloon:",  # ":white_circle:",
                           "text": "neutralized",
                           },
}

validations: List[Dict[str, Any]] = [
    {"name": "wc-test",
     "estimate_time": 10,
     "good_link": "https://crt.prod.linkedin.com/#/testing/executions/b9918fde-40ab-4f51-86a0-8e8edf25debc/execution",
     "bad_link": "https://crt.prod.linkedin.com/#/testing/executions/143cd0c7-47b3-46f4-be37-e77b58e76082/execution",
     },
    {"name": "mint validate",
     "estimate_time": 3,
     "good_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-13/18/65/65df8523-0961-4447-bf99-352b65484dd7/0/console.log",
     "bad_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-11/23/59/595c4644-a889-4338-b87c-fcc2f18e49a1/0/console.log",
     },
    {"name": "code coverage",
     "estimate_time": 4,
     "good_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-13/18/65/65df8523-0961-4447-bf99-352b65484dd7/0/console.log",
     "bad_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-11/23/59/595c4644-a889-4338-b87c-fcc2f18e49a1/0/console.log",
     },
    {"name": "flake8",
     "estimate_time": 1,
     "language": "python",
     "good_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-13/18/65/65df8523-0961-4447-bf99-352b65484dd7/0/console.log",
     "bad_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-11/23/59/595c4644-a889-4338-b87c-fcc2f18e49a1/0/console.log",
     },
    {"name": "mypy",
     "estimate_time": 5,
     "language": "python",
     "good_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-13/18/65/65df8523-0961-4447-bf99-352b65484dd7/0/console.log",
     "bad_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-11/23/59/595c4644-a889-4338-b87c-fcc2f18e49a1/0/console.log",
     },
    {"name": "xss",
     "estimate_time": 6,
     "language": "javascript",
     "good_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-13/18/65/65df8523-0961-4447-bf99-352b65484dd7/0/console.log",
     "bad_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-11/23/59/595c4644-a889-4338-b87c-fcc2f18e49a1/0/console.log",
     },
    {"name": "checkstyle",
     "estimate_time": 2,
     "language": "java",
     "good_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-13/18/65/65df8523-0961-4447-bf99-352b65484dd7/0/console.log",
     "bad_link": "http://cia-file-store.corp.linkedin.com:1177/files/20-03-11/23/59/595c4644-a889-4338-b87c-fcc2f18e49a1/0/console.log",
     },
]