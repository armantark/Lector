import re

import requests
from bs4 import BeautifulSoup

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
            'https://armenianscripture.wordpress.com/%Y/%m/%-d/').lower()
        synaxarium_url = self.today.strftime('https://ststepanos.org/calendars/category/feastsofsaints/%Y-%m-%d/')

        if self.url is None:
            logger.error('Failed to generate Armenian lectionary URL')

        # Fetch the initial page
        initial_soup = self.fetch_and_parse_html(self.url)
        if initial_soup is None:
            logger.error(f'Failed to fetch initial Armenian lectionary page: {self.url}')
            return

        # Find the "Continue reading →" link
        continue_reading_link = self.extract_continue_reading_url(initial_soup)
        if continue_reading_link is None:
            logger.error(f'No "Continue reading" link found on Armenian lectionary page: {self.url}')
            return

        # Fetch the linked page
        self.url = continue_reading_link
        soup = self.fetch_and_parse_html(self.url)
        if soup is None:
            logger.error(f'Failed to fetch detailed Armenian lectionary page: {self.url}')
            return

        # Extract all required content
        self.title = self.extract_title(soup)
        self.subtitle = self.extract_subtitle(soup)
        self.readings = self.extract_readings(soup)
        
        # Try to fetch synaxarium from different possible URLs
        self.synaxarium = self.get_synaxarium(synaxarium_url)
        if not self.synaxarium:
            logger.debug('No feasts of saints found, checking dominical feasts')
            synaxarium_url = self.today.strftime(
                'https://ststepanos.org/calendars/category/dominicalfeasts/%Y-%m-%d/')
            self.synaxarium = self.get_synaxarium(synaxarium_url)
            
        if not self.synaxarium:
            logger.debug('No dominical feasts found, checking church celebrations')
            synaxarium_url = self.today.strftime(
                'https://ststepanos.org/calendars/category/churchcelebrations/%Y-%m-%d/')
            self.synaxarium = self.get_synaxarium(synaxarium_url)

        self.ready = True

    @staticmethod
    def extract_continue_reading_url(soup):
        for tag in soup.find_all('a'):
            if 'continue reading' in tag.get_text().lower():
                return tag.get('href')
        return None

    def extract_title(self, soup):
        # Define the different selectors we'll be using in order of preference
        selectors = ['h3', 'p', 'p strong']

        # Initialize title to an empty string
        title = ''

        # Loop through each selector to find a title
        for selector in selectors:
            elements = soup.select(selector)
            if len(elements) > 0:
                # Manually convert <br/> tags to line breaks
                for br in elements[0].find_all("br"):
                    br.replace_with("\n")

                title = elements[0].text.strip()

                # If the title does not contain "Share this:", we've found a good title
                if "Share this:" not in title and title != '':
                    break

        # Replace commas without spaces after them with ',\n'
        title_with_newlines = re.sub(r',(?!\s)', ',\n', title)

        return title_with_newlines

    def extract_subtitle(self, soup):
        return date_expand.auto_expand(self.today, self.title)

    def extract_readings(self, soup):
        # Initialize
        selectors = ['h3', 'p']
        readings = ''
        readings_list = []
        bible_verse_regex = re.compile(r'\b[A-Za-z\s]+\d+:\d+(?:-\d+(?::\d+)?)?\b')

        # Loop through each selector to find suitable readings
        for selector in selectors:
            readings_raw_select = soup.select(selector)

            if readings_raw_select:
                readings = '\n'.join(str(content).strip() for content in readings_raw_select)
                readings = readings.replace('<br/>', '\n')  # Remove or replace HTML tags if needed

                # Check for suitable readings and break if found
                if bible_verse_regex.search(readings):
                    readings_list = bible_verse_regex.findall(readings)
                    break

        # Remove duplicates and clean up readings
        readings_list = list(dict.fromkeys(x.strip() for x in readings_list))
        # Return if no readings are found
        if not readings_list:
            return ["[No readings for this day]"]

        # Perform substitutions
        for original, substitute in self.SUBSTITUTIONS.items():
            readings_list = [reading.replace(original, substitute) for reading in readings_list]

        return readings_list

    @staticmethod
    def _get_notes_url(r, soup):
        if len(r.history) == 0:
            attachment_link = soup.select_one("p[class='attachment']>a")
            return attachment_link['href'] if attachment_link else ''
        else:
            return ''

    @staticmethod
    def get_synaxarium(url):
        """
        Get the daily synaxarium (and implicit color)
        """
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

        json = [
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
        return json

    def _build_description(self):
        synaxarium = f'[Synaxarium]({self.synaxarium})\n\n' if self.synaxarium else ''
        readings = '\n'.join(
            bible_url.convert(reading) if reading != '[No readings for this day]' else reading
            for reading in self.readings
        )
        notes = f"\n\n*[Notes]({self.notes_url})" if self.notes_url else ''

        return synaxarium + readings + notes
