import datetime
import re

import requests
from bs4 import BeautifulSoup

from helpers import bible_url, date_expand
from helpers.bible_reference import normalize_usccb_reference
from helpers.logger import get_logger
from lectionary.base import Lectionary

_logger = get_logger(__name__)


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
            _logger.error(f'Failed to make request: {e}', exc_info=True)
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
        """Normalize a USCCB Bible reference using the shared helper."""
        return normalize_usccb_reference(reference)


class CatholicLectionary(Lectionary):
    """
    Catholic Lectionary implementation.
    
    This lectionary is unique in that it uses CatholicPage objects to represent
    multiple pages of readings, rather than a single list of readings.
    """

    def __init__(self):
        super().__init__()  # Initialize base class attributes (today, url, ready, last_regeneration, etc.)
        self.permalink = self.today.strftime('https://bible.usccb.org/bible/readings/%m%d%y.cfm')
        self.url = self.permalink  # Set base class url to permalink for consistency
        self.pages = []
        self.color = 0
        self.regenerate()

    def clear(self):
        super().clear()  # Clear base class attributes
        self.color = 0
        self.pages = []
        self.permalink = ''

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
        super().regenerate()  # Update last_regeneration and today from base class
        self.permalink = self.today.strftime('https://bible.usccb.org/bible/readings/%m%d%y.cfm')
        self.url = self.permalink  # Keep base class url in sync
        self.pages = []

        page_content = self._fetch_page_content(self.permalink)
        if page_content is None:
            self.clear()
            return

        if self._append_page_if_ready(page_content):
            self._append_linked_pages(page_content)
            self.color = self.get_color()
            self.ready = True
        else:
            self.clear()

    # Abstract method implementations (Catholic lectionary uses pages instead of these)
    def extract_title(self, soup):
        pass  # Title is extracted per-page in CatholicPage

    def extract_subtitle(self, soup):
        pass  # Subtitle is extracted per-page in CatholicPage

    def extract_readings(self, soup):
        pass  # Readings are extracted per-page in CatholicPage

    def extract_synaxarium(self, soup):
        pass  # Not used by Catholic lectionary

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
