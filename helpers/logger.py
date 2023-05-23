import logging
import os

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


def log(message):
    log_webhook = os.environ['log_webhook']

    if log_webhook != '':
        requests.post(log_webhook, json={
            "content": message
        })
