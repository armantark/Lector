import datetime

import requests
from bs4 import BeautifulSoup

from helpers import bible_url, date_expand


class BookOfCommonPrayer:
    def __init__(self):
        self.ready = None
        self._reset()

    def _reset(self):
        self.ready = False
        self._today = datetime.date.today()
        self._url = self._today.strftime('https://www.biblegateway.com/reading-plans/bcp-daily-office/%Y/%m/%d')
        self._title = ''
        self._readings = []

    def _fetch_content(self):
        try:
            response = requests.get(self._url)
            if response.status_code != 200:
                return None
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException:
            return None

    def _extract_information(self, soup):
        self._title = f'Daily Readings for {date_expand.expand(self._today)}'
        self._readings = [
            reading.text
            for reading in soup.select("[class='rp-passage-display']")
        ]

    def regenerate(self):
        self._reset()
        soup = self._fetch_content()

        if soup is None:
            return

        self._extract_information(soup)
        self.ready = True

    def build_json(self):
        """
        Build Discord embed json representing the calendar entry
        """
        if not self.ready:
            return []

        return [{
            'title': self._title,
            'description': '\n'.join(bible_url.convert(reading) for reading in self._readings),
            'footer': {'text': 'Copyright © BibleGateway.'},
            'author': {
                'name': 'The Book of Common Prayer',
                'url': self._url
            }
        }]
