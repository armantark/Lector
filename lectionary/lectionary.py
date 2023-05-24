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
        pass

    def fetch_and_parse_html(self, url):
        try:
            r = requests.get(url)
            if r.status_code != 200:
                self.clear()
                return None
        except requests.RequestException:
            self.clear()
            return None

        return BeautifulSoup(r.text, 'html.parser')

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
