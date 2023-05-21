import os

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.


class Config:
    def __init__(self):
        self.prefix = os.getenv('prefix')
        self.token = os.getenv('token')
        self.log_webhook = os.getenv('log_webhook')
