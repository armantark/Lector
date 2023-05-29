import re

from helpers import bible_url, logger
from lectionary.lectionary import Lectionary

logger = logger.get_logger(__name__)


class OrthodoxRussianLectionary(Lectionary):
    def extract_synaxarium(self, soup):
        pass

    BASE_URL = 'https://holytrinityorthodox.com/calendar/calendar.php'

    def __init__(self):
        super().__init__()
        self.saints = None
        self.troparion = None
        self.subtitles = None
        self.regenerate()

    def clear(self):
        super().clear()
        self.saints = None
        self.troparion = None
        self.subtitles = None

    def regenerate(self):
        super().regenerate()
        self.url = self._build_calendar_url()

        soup = self.fetch_and_parse_html(self.url)
        if soup is not None:
            try:
                self.title = self.extract_title(soup)
                self.subtitles = self.extract_subtitle(soup)
                self.saints = self.extract_saints(soup)
                self.readings = self.extract_readings(soup)
                self.troparion = self._extract_troparion(soup)
                self.ready = True
            except Exception as e:
                logger.error(f"Failed to parse the webpage: {e}", exc_info=True)

    def _build_calendar_url(self):
        url = f'{self.BASE_URL}' \
              f'?month={self.today.month}' \
              f'&today={self.today.day}' \
              f'&year={self.today.year}' \
              f'&dt=1&header=1&lives=1&trp=2&scripture=2'
        return url

    def extract_title(self, soup):
        return soup.select_one('span[class="dataheader"]').text

    def extract_subtitle(self, soup):
        a = soup.select_one('span[class="headerheader"]').text
        b = soup.select_one('span[class="headerheader"]>span').text.strip()
        return [item for item in [a.replace(b, '').strip(), b] if item]

    @staticmethod
    def extract_saints(soup):
        return [
            item
            for item in soup.select_one('span[class="normaltext"]').text.split('\n')
            if item  # Rid the list of empty strings
        ]

    def extract_readings(self, soup):
        readings_elements = soup.select('span[class="normaltext"]')
        if len(readings_elements) < 2:  # make sure there are at least two elements
            logger.error("Couldn't find the readings on the page")
            return None
        readings_element = readings_elements[1]  # it seems the readings are in the second 'normaltext' span
        readings = [str(item) for item in readings_element.contents]
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
            'description': bible_url.html_convert(''.join(self.readings)),
        }

    def _build_troparion_embed(self):
        return {
            'title': 'Troparion',
            'footer': {'text': '© Holy Trinity Russian Orthodox Church'},
            'fields': [{'name': saint, 'value': troparion, 'inline': False} for saint, troparion in
                       self.troparion.items()],
        }
