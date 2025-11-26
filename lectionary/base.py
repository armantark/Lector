# todo: make a generic lectionary class that all the others inherit from
# so it's easier to make new ones
import datetime
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup


class Lectionary(ABC):
    """
    Abstract Base Class for a lectionary.
    """

    def __init__(self):
        self.today = datetime.date.today()
        self.url = ''
        self.title = ''
        self.subtitle = ''
        self.readings = []
        self.synaxarium = []
        self.ready = False
        self.last_regeneration = datetime.datetime.min

    def clear(self):
        self.today = None
        self.url = ''
        self.title = ''
        self.subtitle = ''
        self.readings = []
        self.synaxarium = []
        self.ready = False

    @abstractmethod
    def regenerate(self):
        self.last_regeneration = datetime.datetime.now()
        self.today = datetime.date.today()
        pass

    def fetch_and_parse_html(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                return None
        except requests.RequestException:
            return None

        return BeautifulSoup(r.text, 'html.parser')

    @abstractmethod
    def extract_title(self, soup):
        pass

    @abstractmethod
    def extract_subtitle(self, soup):
        pass

    @abstractmethod
    def extract_readings(self, soup):
        pass

    @abstractmethod
    def extract_synaxarium(self, soup):
        pass

    @abstractmethod
    def build_json(self):
        pass
