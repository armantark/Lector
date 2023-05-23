import datetime

import requests
from bs4 import BeautifulSoup

from helpers import bible_url
from helpers import date_expand
from helpers.logger import log


class OrthodoxGreekLectionary:
    """
    Class representing the data scraped from the Orthodox calendar provided by
    the Greek Orthodox Archdiocese of America.
    (https://www.goarch.org/chapel/calendar)
    """

    def __init__(self):
        self.today = None
        self.url = None
        self.title = None
        self.fast = None
        self.saints_feasts = None
        self.readings = None
        self.icon_url = None
        self.ready = False
        self.regenerate()

    def clear(self):
        self.today = None
        self.url = ''
        self.title = ''
        self.fast = []
        self.saints_feasts = []
        self.readings = []
        self.icon_url = ''
        self.ready = False

    def regenerate(self):
        try:
            self.today = datetime.date.today()
            self.url = self.today.strftime('https://www.goarch.org/chapel?date=%m/%d/%Y')
            self.title = date_expand.expand(self.today)
            r = requests.get(self.url, headers={'User-Agent': 'User'})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')

            icon_element = soup.select_one('[class="commemorate-left"]>div>img')
            if icon_element is None:
                raise Exception("Unable to locate icon on webpage.")
            self.icon_url = icon_element['src']

            fast_element = soup.select_one('[class="oc-fasting"]')
            if fast_element is None:
                raise Exception("Unable to locate fasting information on webpage.")
            self.fast = fast_element.text.strip().split(' | ')

            readings_element = soup.select_one('[class="oc-readings"]')
            if readings_element is None:
                raise Exception("Unable to locate reading information on webpage.")
            raw_readings = readings_element.text.split('\n' * 7)
            readings = [item.strip().replace(' Reading', '') for item in raw_readings]
            self.readings = [f'{item[0]} <a>{item[1]}</a>' for item in [line.split('\n\n') for line in readings]]

            url = self.today.strftime('https://www.goarch.org/chapel/search?month=%m&day=%d')
            log(url)
            r = requests.get(url, headers={'User-Agent': ''})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            self.saints_feasts = [(f'[{item.a.text}]({item.a["href"]})' if item.a else item.span.text) for item in soup.select('[class="ss-result-element"]')]

            self.ready = True

        except Exception as e:
            log(f"An error occurred while scraping the Greek Orthodox Lectionary: {str(e)}")
            self.clear()

    def build_json(self):
        if not self.ready: return []

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
