import logging
import os
import traceback

import requests


def get_logger(name):
    # Create a custom logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create console handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)

    # Create formatter and add it to handler
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)

    # Add handler to the logger
    logger.addHandler(c_handler)

    return logger


class ContextFilter(logging.Filter):
    """
    This is a filter that injects stack info in the LogRecord.
    """

    def filter(self, record):
        record.stack = traceback.format_stack()
        return True


log_filter = ContextFilter()

# In your main function or wherever you setup your logging
# Add the filter to root logger
logging.getLogger().addFilter(log_filter)


def log(message):
    log_webhook = os.environ['log_webhook']

    if log_webhook != '':
        requests.post(log_webhook, json={
            "content": message
        })
