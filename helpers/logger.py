import os

import requests


def log(message):
    log_webhook = os.environ['log_webhook']

    if log_webhook != '':
        requests.post(log_webhook, json={
            "content": message
        })
