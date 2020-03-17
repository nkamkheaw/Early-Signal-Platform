import logging

from checks import ProcessCheckRun, neutralize_latest_check_suite

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
    check_suite = ProcessCheckRun(webhook)
    check_suite.start()


def check_suite_override_handler(webhook):
    """Override the check runs so that the PR can be merged."""
    neutralize_latest_check_suite(webhook)
