import datetime
import re

import requests
from bs4 import BeautifulSoup

from helpers import bible_url, logger

logger = logger.get_logger(__name__)


class OrthodoxRussianLectionary:
    BASE_URL = 'https://holytrinityorthodox.com/calendar/calendar.php'

    def __init__(self):
        self.url = None
        self.today = None
        self.ready = None
        self._reset_attributes()
        self.regenerate()

    def _reset_attributes(self):
        self.today = None
        self.url = ''
        self.title = ''
        self.subtitles = []
        self.saints = []
        self.readings = []
        self.troparion = {}
        self.ready = False

    def clear(self):
        self._reset_attributes()

    def regenerate(self):
        self.today = datetime.date.today()
        self.url = self._build_calendar_url()

        page_content = self._fetch_page_content()
        if page_content is not None:
            self._scrape_page_content(page_content)
            self.ready = True

    def _build_calendar_url(self):
        url = f'{self.BASE_URL}' \
              f'?month={self.today.month}' \
              f'&today={self.today.day}' \
              f'&year={self.today.year}' \
              f'&dt=1&header=1&lives=1&trp=2&scripture=2'
        logger.debug(url)
        return url

    def _fetch_page_content(self):
        try:
            r = requests.get(self.url)
            r.raise_for_status()
            return r.text
        except requests.exceptions.HTTPError as errh:
            logger.error(f"HTTP Error: {errh}", exc_info=True)
            return None
        except requests.exceptions.ConnectionError as errc:
            logger.error(f"Error Connecting: {errc}", exc_info=True)
            return None
        except requests.exceptions.Timeout as errt:
            logger.error(f"Timeout Error: {errt}", exc_info=True)
            return None
        except requests.exceptions.RequestException as err:
            logger.error(f"Something Else: {err}", exc_info=True)
            return None

    def _scrape_page_content(self, page_content):
        try:
            soup = BeautifulSoup(page_content, 'html.parser')
            self.title, self.subtitles = self._extract_title_and_subtitles(soup)
            self.saints = self._extract_saints(soup)
            self.readings = self._extract_readings(soup)
            self.troparion = self._extract_troparion(soup)
        except Exception as e:
            logger.error(f"Failed to parse the webpage: {e}", exc_info=True)

    @staticmethod
    def _extract_title_and_subtitles(soup):
        title = soup.select_one('span[class="dataheader"]').text
        a = soup.select_one('span[class="headerheader"]').text
        b = soup.select_one('span[class="headerheader"]>span').text
        subtitles = [item for item in [a.replace(b, ''), b.strip()] if item]
        return title, subtitles

    @staticmethod
    def _extract_saints(soup):
        return [
            item
            for item in soup.select_one('span[class="normaltext"]').text.split('\n')
            if item  # Rid the list of empty strings
        ]

    @staticmethod
    def _extract_readings(soup):
        readings = soup.select_one('span[class="normaltext"]:nth-child(5)')
        readings = [str(item) for item in readings.contents]
        readings = ''.join(readings).replace('\n', '').replace('<br/>', '\n').strip()
        readings = re.sub(r'<a.*>([^<>]*)</a>', r'<a>\1</a>', readings)  # Collapse the Bible links to what's necessary
        readings = re.sub(r'<em>([^<>]*)</em>', r'*\1*', readings)  # Italicize lines that are wrapped in the <em> tag
        if isinstance(readings, list):  # Check if readings is a list. If so, join it into a string.
            readings = ' '.join(readings)
        return readings

    @staticmethod
    def _extract_troparion(soup):
        keys = [item.text for item in soup.select('p > b:first-child')]
        values = [item.text for item in soup.select('span[class="normaltext"] > p')]
        values = [value.replace(key, '') for key, value in zip(keys, values)]
        keys = [key.replace('\n', '').replace('\r', '').replace(' —', '') for key in keys]
        values = [value.replace('\n', '').replace('\r', '') for value in values]
        return dict(zip(keys, values))

    def build_json(self):
        if not self.ready:
            return []

        return [
            self._build_main_embed(),
            self._build_saints_embed(),
            self._build_readings_embed(),
            self._build_troparion_embed(),
        ]

    def _build_main_embed(self):
        return {
            'title': self.title,
            'description': '\n'.join(self.subtitles),
            'author': {'name': 'Russian Orthodox Lectionary', 'url': self.url},
        }

    def _build_saints_embed(self):
        return {
            'title': 'Saints & Feasts',
            'description': '\n'.join(self.saints),
        }

    def _build_readings_embed(self):
        return {
            'title': 'The Scripture Readings',
            'description': bible_url.html_convert(' '.join(self.readings)),
        }

    def _build_troparion_embed(self):
        return {
            'title': 'Troparion',
            'footer': {'text': '© Holy Trinity Russian Orthodox Church'},
            'fields': [{'name': saint, 'value': troparion, 'inline': False} for saint, troparion in
                       self.troparion.items()],
        }
