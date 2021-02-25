import requests
import json
import os

def log(message):
    log_webhook = os.environ['log_webhook']

    if log_webhook != '':
        requests.post(log_webhook, json={
            "content":message
        })