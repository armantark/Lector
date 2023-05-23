import datetime
import re

import requests
from bs4 import BeautifulSoup

from helpers import bible_url, date_expand, logger

logger = logger.get_logger(__name__)


class CatholicPage:
    """
    A class that takes in the link, and possibly the raw HTML, for a Catholic
    readings page, scrapes the key info, and uses this as its attributes
    """

    def __init__(self, today, url, source_text=None):
        self.sections = None
        self.footer = None
        self.ready = None
        self.footer = None
        self.ready = None
        self.desc = None
        self.title = None
        self.today = today
        self.url = url
        self.clear()

        if source_text is None:
            r = self._make_request(url)
            if r is None:
                return
            source_text = r.text

        self.parse_source_text(source_text)

    def clear(self):
        self.url = ''
        self.title = ''
        self.desc = ''
        self.sections = {}
        self.footer = ''
        self.ready = False

    @staticmethod
    def _make_request(url):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return r
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to make request: {e}', exc_info=True)
            return None

    def parse_source_text(self, source_text):
        soup = BeautifulSoup(source_text, 'html.parser')
        self.title = soup.title.text.replace(' | USCCB', '')
        self.footer = soup.select_one('h2 ~ p').text.strip()
        self.desc = date_expand.auto_expand(self.today, self.title)

        blocks = soup.select('.b-verse>div>div>div>div')
        for block in blocks:
            self._parse_block(block)

        self.ready = True

    def _parse_block(self, block):
        header = block.select_one('h3').text.strip()
        header = 'Gospel' if header == '' else header
        lines = self._parse_links(block.select('a'))

        if lines:
            self.sections[header] = ' or\n'.join(lines)

    def _parse_links(self, links):
        formatted_lines = []
        for link in links:
            link = link.text.strip().title()
            if link:
                link = self._format_link(link)
                formatted_lines.append(link)
        return formatted_lines

    def _format_link(self, link):
        link = link.replace('.', '').replace(u'\xa0', u' ').replace(' And ', ', ')
        if link[0] in list('0123456789') and link[:2] not in ['1 ', '2 ', '3 ']:
            link = 'Ps ' + link
        return f'<a>{self._clean_ref(link)}</a>'

    @staticmethod
    def _clean_ref(reference):
        substitutions = {
            'GN': 'Genesis',
            'EX': 'Exodus',
            'LV': 'Leviticus',
            'NM': 'Numbers',

            'JDT': 'Judith',  # This gets moved up so the proper substitution is made
            'DT': 'Deuteronomy',

            'JOS': 'Joshua',
            'JGS': 'Judges',
            'RU': 'Ruth',
            '1 SM': '1 Samuel',
            '2 SM': '2 Samuel',
            '1 KGS': '1 Kings',
            '2 KGS': '2 Kings',
            '1 CHR': '1 Chronicles',
            '2 CHR': '2 Chronicles',
            'EZR': 'Ezra',
            'NEH': 'Nehemiah',

            'TB': 'Tobit',
            #           Judith
            'EST': 'Esther',
            '1 MC': '1 Maccabees',
            '2 MC': '2 Maccabees',

            'JB': 'Job',
            'PS': 'Psalm',
            'PRV': 'Proverbs',
            'ECCL': 'Ecclesiastes',
            'SGS': 'Song of Songs',
            'WIS': 'Wisdom',
            'SIR': 'Sirach',

            'IS': 'Isaiah',
            'JER': 'Jeremiah',
            'LAM': 'Lamentations',
            'BAR': 'Baruch',
            'EZ': 'Ezekiel',
            'DN': 'Daniel',
            'HOS': 'Hosea',
            'JL': 'Joel',
            'AM': 'Amos',
            'OB': 'Obadiah',
            'JON': 'Jonah',
            'MI': 'Micah',
            'NA': 'Nahum',
            'HB': 'Habakkuk',
            'ZEP': 'Zephaniah',
            'HG': 'Haggai',
            'ZEC': 'Zachariah',
            'MAL': 'Malachi',

            'MT': 'Matthew',
            'MK': 'Mark',
            'LK': 'Luke',
            'JN': 'John',

            'ACTS': 'Acts',

            'ROM': 'Romans',
            '1 COR': '1 Corinthians',
            '2 COR': '2 Corinthians',
            'GAL': 'Galatians',
            'EPH': 'Ephesians',
            'PHIL': 'Philippians',
            'COL': 'Colossians',
            '1 THES': '1 Thessalonians',
            '2 THES': '2 Thessalonians',
            '1 TM': '1 Timothy',
            '2 TM': '2 Timothy',
            'TI': 'Titus',
            'PHLM': 'Philemon',
            'HEB': 'Hebrews',

            'JAS': 'James',
            '1 PT': '1 Peter',
            '2 PT': '2 Peter',
            '1 JN': '1 John',
            '2 JN': '2 John',
            '3 JN': '3 John',
            'JUDE': 'Jude',
            'RV': 'Revelation'
        }

        reference = reference.upper()
        for original in substitutions.keys():
            if f'{original} ' in reference:
                reference = reference.replace(original, substitutions[original])
                break
        return reference.title()


class CatholicLectionary:
    def __init__(self):
        self.today = datetime.date.today()
        self.permalink = self.today.strftime('https://bible.usccb.org/bible/readings/%m%d%y.cfm')
        self.pages = []
        self.color = self.get_color()
        self.ready = self.regenerate()

    def clear(self):
        self.today = None
        self.color = 0
        self.pages = []
        self.ready = False

    def get_color(self):
        color_mappings = {
            'red': 0xEE4540,
            'green': 0x03AA5D,
            'white': 0xFFFFFE,  # Pure white doesn't work :/
            'violet': 0x9059AA,
            'pink': 0xF9539F
        }

        try:
            r = requests.get('https://www.divinemercyrosary.com/roman-calendar.php')
            r.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
            return color_mappings['green']

        color_today = re.search(rf'<td>{self.today.strftime("%B %d")}.*?<td.*?bgcolor=(.*?)"', r.text, re.DOTALL)
        if color_today is not None:
            color = color_today.group(1).lower()
            return color_mappings[color]
        else:
            return color_mappings['green']

    def regenerate(self):
        self.today = datetime.date.today()
        self.permalink = self.today.strftime('https://bible.usccb.org/bible/readings/%m%d%y.cfm')
        self.pages = []

        page_content = self._fetch_page_content(self.permalink)
        if page_content is None:
            self.clear()
            return False

        if self._append_page_if_ready(page_content):
            self._append_linked_pages(page_content)
            self.color = self.get_color()
            self.ready = True
            return True
        else:
            self.clear()
            return False

    @staticmethod
    def _fetch_page_content(url):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return r.text
        except requests.exceptions.RequestException:
            pass
        return None

    def _append_page_if_ready(self, page_content):
        page = CatholicPage(self.today, self.permalink, page_content)
        if page.ready:
            self.pages.append(page)
            return True
        return False

    def _append_linked_pages(self, page_content):
        linked_page_urls = self._extract_linked_page_urls(page_content)
        for url in linked_page_urls:
            page = CatholicPage(self.today, url)
            if page.ready:
                self.pages.append(page)

    @staticmethod
    def _extract_linked_page_urls(page_content):
        links = re.findall(r'/bible/readings/[0-9]{4}[a-z-]+\.cfm', page_content)
        return ['https://bible.usccb.org' + link if 'https://' != link[:8] else link for link in links]

    def build_json(self):
        if not self.ready:
            return []

        return [self._build_embed_for_page(page) for page in self.pages]

    def _build_embed_for_page(self, page):
        return {
            'title': page.title,
            'description': page.desc,
            'color': self.color,
            'footer': {'text': page.footer + '\nCopyright © USCCB.'},
            'author': {'name': 'Catholic Lectionary', 'url': page.url},
            'fields': self._build_fields_for_page(page),
        }

    @staticmethod
    def _build_fields_for_page(page):
        return [{'name': header, 'value': bible_url.html_convert(page.sections[header]), 'inline': False}
                for header in page.sections]
