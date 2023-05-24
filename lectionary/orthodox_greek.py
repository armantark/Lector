from helpers import bible_url
from helpers import date_expand
from helpers.logger import log
from lectionary.lectionary import Lectionary


class OrthodoxGreekLectionary(Lectionary):
    """
    Class representing the data scraped from the Orthodox calendar provided by
    the Greek Orthodox Archdiocese of America.
    (https://www.goarch.org/chapel/calendar)
    """

    def extract_title(self, soup):
        return date_expand.expand(self.today)

    def extract_subtitle(self, soup):
        pass

    def extract_synaxarium(self, soup):
        pass

    def __init__(self):
        super().__init__()
        self.fast = None
        self.saints_feasts = None
        self.icon_url = None
        self.regenerate()

    def clear(self):
        super().clear()
        self.fast = []
        self.saints_feasts = []
        self.icon_url = ''

    def regenerate(self):
        try:
            self.url = self.today.strftime('https://www.goarch.org/chapel?date=%m/%d/%Y')
            self.title = self.extract_title(None)
            soup = self.fetch_and_parse_html(self.url)
            if soup is None:
                raise Exception("Unable to get data from the url")

            self.icon_url = self.extract_icon_url(soup)
            self.fast = self.extract_fast(soup)
            self.readings = self.extract_readings(soup)

            url = self.today.strftime('https://www.goarch.org/chapel/search?month=%m&day=%d')
            soup = self.fetch_and_parse_html(url)
            if soup is None:
                raise Exception("Unable to get data from the url")
            self.saints_feasts = self.extract_saints_feasts(soup)

            self.ready = True

        except Exception as e:
            log(f"An error occurred while scraping the Greek Orthodox Lectionary: {str(e)}")
            self.clear()

    @staticmethod
    def extract_icon_url(soup):
        icon_element = soup.select_one('[class="commemorate-left"]>div>img')
        if icon_element is None:
            raise Exception("Unable to locate icon on webpage.")
        return icon_element['src']

    @staticmethod
    def extract_fast(soup):
        fast_element = soup.select_one('[class="oc-fasting"]')
        if fast_element is None:
            raise Exception("Unable to locate fasting information on webpage.")
        return fast_element.text.strip().split(' | ')

    def extract_readings(self, soup):
        readings_element = soup.select_one('[class="oc-readings"]')
        if readings_element is None:
            raise Exception("Unable to locate reading information on webpage.")
        raw_readings = readings_element.text.split('\n' * 7)
        readings = [item.strip().replace(' Reading', '') for item in raw_readings]
        return [f'{item[0]} <a>{item[1]}</a>' for item in [line.split('\n\n') for line in readings]]

    @staticmethod
    def extract_saints_feasts(soup):
        return [(f'[{item.a.text}]({item.a["href"]})' if item.a else item.span.text) for item in
                soup.select('[class="ss-result-element"]')]

    def build_json(self):
        if not self.ready:
            return [
                {
                    'title': 'Greek Orthodox Lectionary',
                    'color': 0xA68141,  # Golden brown
                    'footer': {'text': 'Sorry for the inconvenience.'},
                    'author': {
                        'name': 'Greek Orthodox Lectionary',
                        'url': self.url
                    },
                    'fields': [
                        {
                            'name': 'This lectionary is not currently supported',
                            'value': 'Due to a change in the website structure, '
                                     'this lectionary is not currently supported. '
                                     'We are trying to find another source in the meantime.',
                            'inline': False
                        }
                    ]
                }
            ]

        return [
            {
                'title': self.title,
                'color': 0xA68141,  # Golden brown
                'footer': {'text': 'Copyright © 2017 Greek Orthodox Archdiocese of America.'},
                'thumbnail': {'url': self.icon_url},
                'author': {
                    'name': 'Greek Orthodox Lectionary',
                    'url': self.url
                },
                'fields': [
                    {
                        'name': self.fast[0],
                        'value': self.fast[1],
                        'inline': False
                    },
                    {
                        'name': 'Saints & Feasts',
                        'value': '\n'.join([f'• {item}' for item in self.saints_feasts]),
                        'inline': False
                    },
                    {
                        'name': 'Scripture Readings',
                        'value': bible_url.html_convert('\n'.join(self.readings)),
                        'inline': False
                    }
                ]
            }
        ]
