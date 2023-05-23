import datetime
import logging

import requests
from bs4 import BeautifulSoup, NavigableString

from helpers import bible_url, date_expand

# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)

# Add handler to the logger
logger.addHandler(c_handler)


class ArmenianLectionary:
    SUBSTITUTIONS = {
        'III ': '3 ',
        'II ': '2 ',
        'I ': '1 ',
        'Azariah': 'Prayer of Azariah'
    }

    def __init__(self):
        self.notes_url = None
        self.subtitle = None
        self.today = None
        self.url = ''
        self.title = ''
        self.description = ''
        self.readings = []
        self.synaxarium = ''
        self.ready = False
        self.regenerate()

    def clear(self):
        self.today = None
        self.url = ''
        self.title = ''
        self.description = ''
        self.readings = []
        self.synaxarium = ''
        self.ready = False

    def get_synaxarium(self):
        """
        Get the daily synaxarium (and implicit color)
        """
        url = self.today.strftime('https://www.qahana.am/en/holidays/%Y-%m-%d/1')

        try:
            r = requests.get(url, headers={'User-Agent': ''})
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to get synaxarium: {e}')
            return ''

        soup = BeautifulSoup(r.text, 'html.parser')

        return url if soup.select_one('div[class^="holidayItem"]>h2') else ''

    def regenerate(self):
        self.today = datetime.date.today()
        self.url = self.today.strftime('https://armenianscripture.wordpress.com/%Y/%m/%d/%B-%d-%Y/')

        try:
            r = requests.get(self.url)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.clear()
            logger.error(f'Request failed: {e}')
            return

        soup = BeautifulSoup(r.text, 'html.parser')

        h3_elements = soup.select('h3')
        if len(h3_elements) > 0:
            self.title = h3_elements[0].text
            self.subtitle = date_expand.auto_expand(self.today, self.title)
            readings = self._parse_readings(soup)
            self.readings = readings.split('\n') if readings != '[No readings for this day]' else [readings]
        else:
            self.title = ''
            self.subtitle = ''
            self.readings = []

        self.notes_url = self._get_notes_url(r, soup)
        self.ready = True

    def _parse_readings(self, soup):
        readings_raw_select = soup.select('h3')[1]
        readings = '\n'.join(
            str(content).strip() for content in readings_raw_select.contents if isinstance(content, NavigableString))

        for original, substitute in self.SUBSTITUTIONS.items():
            readings = readings.replace(original, substitute)

        return readings

    @staticmethod
    def _get_notes_url(r, soup):
        if len(r.history) == 0:
            attachment_link = soup.select_one("p[class='attachment']>a")
            return attachment_link['href'] if attachment_link else ''
        else:
            return ''

    def build_json(self):
        if not self.ready:
            logger.warning('Data not ready for JSON build.')
            return []

        return [
            {
                'title': self.title + '\n' + self.subtitle,
                'color': 0xca0000 if self.synaxarium else 0x202225,
                'description': self._build_description(),
                'footer': {'text': 'Copyright © VEMKAR.'},
                'author': {
                    'name': 'Armenian Lectionary',
                    'url': self.url
                }
            }
        ]

    def _build_description(self):
        synaxarium = f'[Synaxarium]({self.synaxarium})\n\n' if self.synaxarium else ''
        readings = '\n'.join(
            bible_url.convert(reading) if reading != '[No readings for this day]' else reading
            for reading in self.readings
        )
        notes = f"\n\n*[Notes]({self.notes_url})" if self.notes_url else ''

        return synaxarium + readings + notes
