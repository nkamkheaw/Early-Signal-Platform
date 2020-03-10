import logging

from constances import NO_VALIDATION_STRING
from gh_utils import ProcessCheckSuite, neutralize_latest_check_suite

"""
SPECIALIZED WEBHOOK HANDLERS 
=======================

Becaue we may receive many webhooks for many different reasons, it"s a good idea
to "hand off" control from `process_message()` to a dedicated function ASAP.

This is a good place for these specialized handlers

"""
log = logging.getLogger(__name__)


def check_suite_request_handler(webhook):
    """Directly create check runs though CheckSuite class right here.
       We might be able to add a logic to kill existing CheckSuite (from previous hash) before kicking off a new one.
    """
    ProcessCheckSuite(webhook)


def check_suite_override_handler(webhook):
    """Override the check runs so that the PR can be merged."""
    for line in str(webhook.comment.body).splitlines():
        if line == NO_VALIDATION_STRING:
            log.info(f"No validation override string detected.")
            neutralize_latest_check_suite(webhook)
            return

    log.debug(f"Ignore the comment.")
