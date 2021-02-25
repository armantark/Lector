import requests
import json

def log(message):
	log_webhook = os.environ['log_webhook']
    # with open('config.json','r') as f:
    #     log_webhook = json.load(f)['log_webhook']

    if log_webhook != '':
        requests.post(log_webhook, json={
            "content":message
        })