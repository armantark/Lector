import re

import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Any

from helpers import bible_url, date_expand
from helpers.logger import get_logger
from lectionary.base import Lectionary

_logger = get_logger(__name__)

# --- Module-level constants ---
ARMENIAN_LECTIONARY_URL_TEMPLATE = "https://armenianscripture.wordpress.com/%Y/%m/%-d/"
SYNAXARIUM_FEASTS_URL_TEMPLATE = (
    "https://ststepanos.org/calendars/category/feastsofsaints/%Y-%m-%d/"
)
SYNAXARIUM_DOMINICAL_URL_TEMPLATE = (
    "https://ststepanos.org/calendars/category/dominicalfeasts/%Y-%m-%d/"
)
SYNAXARIUM_CHURCH_URL_TEMPLATE = (
    "https://ststepanos.org/calendars/category/churchcelebrations/%Y-%m-%d/"
)
ARMENIAN_CHURCH_GE_URL = "https://armenianchurch.ge/en/kalendar-prazdnikov"
BIBLE_VERSE_REGEX = re.compile(r"\b[A-Za-z\s]+\d+:\d+(?:-\d+(?::\d+)?)?\b")


class ArmenianLectionary(Lectionary):
    """
    ArmenianLectionary scrapes and processes daily lectionary readings and synaxarium for the Armenian Church.
    Inherits from the abstract Lectionary base class.
    """

    def extract_synaxarium(self, soup: Any) -> None:
        """
        Placeholder for extracting synaxarium from a soup object (not implemented).
        """
        pass

    SUBSTITUTIONS = {
        "III ": "3 ",
        "II ": "2 ",
        "I ": "1 ",
        "Azariah": "Prayer of Azariah",
    }

    def __init__(self) -> None:
        """
        Initialize the ArmenianLectionary instance and populate its data.
        """
        super().__init__()
        self.notes_url = None
        self.description = ""
        self.synaxarium = ""
        self.regenerate()

    def clear(self) -> None:
        """
        Reset all instance attributes to their default state.
        """
        super().clear()
        self.notes_url = None
        self.description = ""
        self.synaxarium = ""

    def regenerate(self) -> None:
        """
        Regenerate and fetch all lectionary data for today, including readings and synaxarium.
        """
        super().regenerate()  # Update last_regeneration timestamp
        self.url = self.today.strftime(ARMENIAN_LECTIONARY_URL_TEMPLATE).lower()

        initial_soup = self._fetch_initial_soup()
        if initial_soup is None:
            return

        soup = self._follow_continue_reading(initial_soup)
        if soup is None:
            return

        # Extract all required content
        self.title = self.extract_title(soup)
        self.subtitle = self.extract_subtitle(soup)
        self.readings = self.extract_readings(soup)

        # Try to fetch synaxarium from different possible URLs
        self.synaxarium = self._try_synaxarium_urls()
        self.ready = True

    def _fetch_initial_soup(self) -> Optional[Any]:
        """
        Fetch the initial lectionary page and return the parsed soup object.
        """
        if self.url is None or self.url == '':
            _logger.error('Failed to generate Armenian lectionary URL')
            return None
        initial_soup = self.fetch_and_parse_html(self.url)
        if initial_soup is None:
            _logger.error(f'Failed to fetch initial Armenian lectionary page: {self.url}')
            return None
        return initial_soup

    def _follow_continue_reading(self, soup: Any) -> Optional[Any]:
        """
        If a 'Continue reading' link is present, follow it and return the new soup. Otherwise, return the original soup.
        """
        continue_reading_link = self.extract_continue_reading_url(soup)
        if continue_reading_link:
            self.url = continue_reading_link
            soup = self.fetch_and_parse_html(self.url)
            if soup is None:
                _logger.error(f'Failed to fetch detailed Armenian lectionary page: {self.url}')
                return None
        return soup

    def _try_synaxarium_urls(self) -> str:
        """
        Try to fetch synaxarium from multiple possible URLs in order of priority.
        """
        synaxarium_url = self.today.strftime(SYNAXARIUM_FEASTS_URL_TEMPLATE)
        synaxarium = self.get_synaxarium(synaxarium_url)
        if not synaxarium:
            _logger.debug('No feasts of saints found, checking dominical feasts')
            synaxarium_url = self.today.strftime(SYNAXARIUM_DOMINICAL_URL_TEMPLATE)
            synaxarium = self.get_synaxarium(synaxarium_url)
        if not synaxarium:
            _logger.debug('No dominical feasts found, checking church celebrations')
            synaxarium_url = self.today.strftime(SYNAXARIUM_CHURCH_URL_TEMPLATE)
            synaxarium = self.get_synaxarium(synaxarium_url)
        return synaxarium

    @staticmethod
    def extract_continue_reading_url(soup: Any) -> Optional[str]:
        """
        Find and return the URL for the 'Continue reading' link, if present.
        """
        for tag in soup.find_all("a"):
            if "continue reading" in tag.get_text().lower():
                return tag.get("href")
        return None

    def extract_title(self, soup: Any) -> str:
        """
        Extract the title from the soup object using several selectors.
        Returns the title with improved formatting.
        """
        # Define the different selectors we'll be using in order of preference
        selectors = ["h3", "p", "p strong"]

        # Initialize title to an empty string
        title = ""

        # Loop through each selector to find a title
        for selector in selectors:
            elements = soup.select(selector)
            if len(elements) > 0:
                # Manually convert <br/> tags to line breaks
                for br in elements[0].find_all("br"):
                    br.replace_with("\n")

                title = elements[0].text.strip()

                # If the title does not contain "Share this:", we've found a good title
                if "Share this:" not in title and title != "":
                    break

        # Replace commas without spaces after them with ',\n'
        title_with_newlines = re.sub(r",(?!\s)", ",\n", title)

        return title_with_newlines

    def extract_subtitle(self, soup: Any) -> str:
        """
        Generate a subtitle for the lectionary entry based on the date and title.
        """
        return date_expand.auto_expand(self.today, self.title)

    def extract_readings(self, soup: Any) -> List[str]:
        """
        Extract and clean the list of Bible readings from the soup object.
        Returns a list of reading references or a default message if none found.
        """
        # Initialize
        selectors = ["h3", "p"]
        readings = ""
        readings_list = []

        # Loop through each selector to find suitable readings
        for selector in selectors:
            readings_raw_select = soup.select(selector)

            if readings_raw_select:
                readings = "\n".join(
                    str(content).strip() for content in readings_raw_select
                )
                readings = readings.replace(
                    "<br/>", "\n"
                )  # Remove or replace HTML tags if needed

                # Check for suitable readings and break if found
                if BIBLE_VERSE_REGEX.search(readings):
                    readings_list = BIBLE_VERSE_REGEX.findall(readings)
                    break

        # Remove duplicates and clean up readings
        readings_list = list(dict.fromkeys(x.strip() for x in readings_list))
        # Return if no readings are found
        if not readings_list:
            return ["[No readings for this day]"]

        # Perform substitutions
        for original, substitute in self.SUBSTITUTIONS.items():
            readings_list = [
                reading.replace(original, substitute) for reading in readings_list
            ]

        return readings_list

    @staticmethod
    def _get_notes_url(r: Any, soup: Any) -> str:
        """
        Extract the notes URL from the response and soup, if available.
        """
        if len(r.history) == 0:
            attachment_link = soup.select_one("p[class='attachment']>a")
            return attachment_link["href"] if attachment_link else ""
        else:
            return ""

    @staticmethod
    def get_synaxarium(_: str) -> str:
        """
        Get the daily synaxarium link from the Armenian Church calendar website.
        Returns the link as a string, or an empty string if not found.
        """
        import datetime

        today = datetime.date.today()
        try:
            r = requests.get(ARMENIAN_CHURCH_GE_URL, headers={"User-Agent": ""})
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Failed to get synaxarium: {e}", exc_info=True)
            return ""

        soup = BeautifulSoup(r.text, "html.parser")
        events = soup.select(".nb-calendar__event")
        for event in events:
            month_tag = event.select_one(".nb-event__month")
            day_tag = event.select_one(".nb-event__day")
            link_tag = event.select_one("a.nb-event__link")
            if not (month_tag and day_tag and link_tag):
                continue
            month = month_tag.get_text(strip=True)
            day = day_tag.get_text(strip=True)
            # Compare month and day to today
            if (
                month.lower().startswith(today.strftime("%B").lower()[:3])
                or month.lower() == today.strftime("%B").lower()
            ):
                try:
                    if int(day) == today.day:
                        return link_tag["href"]
                except ValueError:
                    continue
        return ""

    def build_json(self) -> List[dict]:
        """
        Build a JSON-serializable representation of the lectionary data for Discord embeds.
        """
        if not self.ready:
            _logger.warning("Data not ready for JSON build.")
            return []

        json = [
            {
                "title": self.title + "\n" + self.subtitle,
                "color": 0xCA0000 if self.synaxarium else 0x202225,
                "description": self._build_description(),
                "footer": {"text": "Copyright © VEMKAR."},
                "author": {"name": "Armenian Lectionary", "url": self.url},
            }
        ]
        return json

    def _build_description(self) -> str:
        """
        Build the description string for the embed, including synaxarium, readings, and notes.
        """
        synaxarium = f"[Synaxarium]({self.synaxarium})\n\n" if self.synaxarium else ""
        readings = "\n".join(
            (
                bible_url.convert(reading)
                if reading != "[No readings for this day]"
                else reading
            )
            for reading in self.readings
        )
        notes = f"\n\n*[Notes]({self.notes_url})" if self.notes_url else ""

        return synaxarium + readings + notes
