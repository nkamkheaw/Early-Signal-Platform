from typing import Any, Dict, List

APP_NAME: str = "Early Signal Platform"

NO_VALIDATION_STRING: str = "NOVALIDATIONOVERRIDE"

CHECK_RUN_STATUS_IN_PROGRESS: str = "in_progress"
CHECK_RUN_STATUS_COMPLETED: str = "completed"
CHECK_RUN_CONCLUSION_SUCCESS: str = "success"
CHECK_RUN_CONCLUSION_FAILURE: str = "failure"
CHECK_RUN_CONCLUSION_NEUTRAL: str = "neutral"


validations: List[Dict[str, Any]] = [
    {"name": "wc-test",
     "estimate_time": 60,
     },
    {"name": "mint validate",
     "estimate_time": 30,
     },
    {"name": "code coverage",
     "estimate_time": 20,
     },
    {"name": "flake8",
     "estimate_time": 10,
     "language": "python",
     },
    {"name": "mypy",
     "estimate_time": 10,
     "language": "python",
     },
    {"name": "xss",
     "estimate_time": 5,
     "language": "javascript",
     },
    {"name": "checkstyle",
     "estimate_time": 10,
     "language": "java",
     },
]