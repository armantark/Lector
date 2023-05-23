import datetime

import requests
from bs4 import BeautifulSoup, NavigableString

from helpers import bible_url, date_expand, logger

logger = logger.get_logger(__name__)


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
        url = self.today.strftime('https://ststepanos.org/calendars/category/dominicalfeasts/%Y-%m-%d/')
        try:
            r = requests.get(url, headers={'User-Agent': ''})
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to get synaxarium: {e}', exc_info=True)
            return ''

        soup = BeautifulSoup(r.text, 'html.parser')

        # Check if the synaxarium link exists on the page
        event_link_element = soup.select_one('h3[class^="tribe-events-list-event-title summary"]>a')
        # Return the link if it exists, else return an empty string
        return url if event_link_element else ''

    def regenerate(self):
        self.today = datetime.date.today()
        self.url = self.today.strftime('https://armenianscripture.wordpress.com/%Y/%m/%d/%B-%d-%Y/')

        try:
            r = requests.get(self.url)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.clear()
            logger.error(f'Request failed: {e}', exc_info=True)
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

        self.synaxarium = self.get_synaxarium()

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
