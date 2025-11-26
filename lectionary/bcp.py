from helpers import bible_url, date_expand
from .base import Lectionary


class BookOfCommonPrayer(Lectionary):
    def extract_subtitle(self, soup):
        pass

    def extract_synaxarium(self, soup):
        pass

    def __init__(self):
        super().__init__()
        self.regenerate()

    def regenerate(self):
        super().regenerate()  # Update last_regeneration timestamp
        self.url = self.today.strftime('https://www.biblegateway.com/reading-plans/bcp-daily-office/%Y/%m/%d')
        soup = self.fetch_and_parse_html(self.url)
        if soup is not None:
            self.title = self.extract_title(soup)
            self.readings = self.extract_readings(soup)
            self.ready = True

    def extract_title(self, soup):
        return f'Daily Readings for {date_expand.expand(self.today)}'

    def extract_readings(self, soup):
        return [
            reading.text
            for reading in soup.select("[class='rp-passage-display']")
        ]

    def build_json(self):
        """
        Build Discord embed json representing the calendar entry
        """
        if not self.ready:
            return []

        return [{
            'title': self.title,
            'description': '\n'.join(bible_url.convert(reading) for reading in self.readings),
            'footer': {'text': 'Source: biblegateway.com'},
            'author': {
                'name': 'The Book of Common Prayer',
                'url': self.url
            }
        }]
