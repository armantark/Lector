import re

import requests
from bs4 import BeautifulSoup, NavigableString

from helpers import bible_url, date_expand, logger
from lectionary.lectionary import Lectionary

logger = logger.get_logger(__name__)


class ArmenianLectionary(Lectionary):
    def extract_synaxarium(self, soup):
        pass

    SUBSTITUTIONS = {
        'III ': '3 ',
        'II ': '2 ',
        'I ': '1 ',
        'Azariah': 'Prayer of Azariah'
    }

    def __init__(self):
        super().__init__()
        self.notes_url = None
        self.description = ''
        self.synaxarium = ''
        self.regenerate()

    def clear(self):
        super().clear()
        self.notes_url = None
        self.description = ''
        self.synaxarium = ''

    def regenerate(self):
        super().regenerate()  # Update last_regeneration timestamp
        self.url = self.today.strftime(
            'https://armenianscripture.wordpress.com/%Y/%m/%-d/').lower() + self.today.strftime('%B-%-d-%Y').lower()
        # self.url = "https://armenianscripture.wordpress.com/2023/06/13/june-13-2023/"
        soup = self.fetch_and_parse_html(self.url)
        if soup is not None:
            self.title = self.extract_title(soup)
            self.subtitle = self.extract_subtitle(soup)
            self.readings = self.extract_readings(soup)
            self.synaxarium = self.get_synaxarium()
            self.ready = True

    def extract_title(self, soup):
        h3_elements = soup.select('h3')
        title = h3_elements[0].text if len(h3_elements) > 0 else ''
        title_with_newlines = re.sub(r',(?!\s)', ',\n', title)
        return title_with_newlines

    def extract_subtitle(self, soup):
        return date_expand.auto_expand(self.today, self.title)

    def extract_readings(self, soup):
        readings_raw_select = soup.select('h3')[1]
        readings = '\n'.join(
            str(content).strip() for content in readings_raw_select.contents if isinstance(content, NavigableString))

        for original, substitute in self.SUBSTITUTIONS.items():
            readings = readings.replace(original, substitute)

        return readings.split('\n') if readings != '[No readings for this day]' else [readings]

    @staticmethod
    def _get_notes_url(r, soup):
        if len(r.history) == 0:
            attachment_link = soup.select_one("p[class='attachment']>a")
            return attachment_link['href'] if attachment_link else ''
        else:
            return ''

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
