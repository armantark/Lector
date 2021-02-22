from helpers import bible_url
from helpers import date_expand

from discord import Embed

from bs4 import BeautifulSoup

import requests
import datetime


class BookOfCommonPrayer:
    def __init__(self): self.regenerate()
    

    def clear(self):
        self.today    = None
        self.url      = ''
        self.title    = ''
        self.readings = ''
        self.ready    = False

    
    def regenerate(self):
        self.today = datetime.date.today()
        self.url   = self.today.strftime('https://www.biblegateway.com/reading-plans/bcp-daily-office/%Y/%m/%d')

        try:
            r = requests.get(self.url)
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear()
            return

        soup = BeautifulSoup(r.text, 'html.parser')

        self.title = f'Daily Readings for {date_expand.expand(self.today)}'
        self.readings = [
            reading.text
            for reading in soup.select("[class='rp-passage-display']")
        ]

        self.ready = True
    

    def build_json(self):
        '''
        Build Discord embed json representing the calendar entry
        '''
        if not self.ready: return []

        return [
            {
                'title':self.title,
                'description':'\n'.join(
                    [
                        bible_url.convert(reading)
                        for reading in self.readings
                    ]
                ),
                'footer':{'text':'Copyright © BibleGateway.'},
                'author':{
                    'name':'The Book of Common Prayer',
                    'url':self.url
                }
            }
        ]