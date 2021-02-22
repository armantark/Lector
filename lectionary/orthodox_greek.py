from helpers import bible_url
from helpers import date_expand

from discord import Colour
from discord import Embed
from bs4 import BeautifulSoup

import requests
import re
import datetime


class OrthodoxGreekLectionary:
    '''
    Class representing the data scraped from the Orthodox calendar provided by
    the Greek Orthodox Archdiocese of America.
    (https://www.goarch.org/chapel/calendar)
    '''

    def __init__(self):
        self.regenerate()


    def clear(self):
        self.today         = None
        self.url           = ''
        self.title         = ''
        self.fast          = []
        self.saints_feasts = []
        self.readings      = []
        self.icon_url      = ''
        self.ready         = False


    def regenerate(self):
        self.today = datetime.date.today()
        self.url   = self.today.strftime('https://www.goarch.org/chapel?date=%m/%d/%Y')

        self.title = date_expand.expand(self.today)

        try:
            # The request needs a 'User-Agent' header, or there will be a 403
            r = requests.get(self.url, headers={'User-Agent':'User'})
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear()
            return
        
        soup = BeautifulSoup(r.text, 'html.parser')

        # Icon url
        self.icon_url = soup.select_one('[class="commemorate-left"]>div>img')['src']

        # Fast
        # This should always be a two-element list
        self.fast = soup.select_one('[class="oc-fasting"]').text.strip().split(' | ')

        # Readings
        # 3 nested list comprehensions feels wrong
        self.readings = [
            f'{item[0]} <a>{item[1]}</a>'
            for item in [
                line.split('\n\n')
                for line in [
                    item.strip().replace(' Reading','')
                    for item in soup.select_one('[class="oc-readings"]').text.split('\n'*7)
                ]
            ]
        ]

        # Second Request for All Saints & Feasts
        url = self.today.strftime('https://www.goarch.org/chapel/search?month=%m&day=%d')

        try:
            r = requests.get(url, headers={'User-Agent':''})
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear()
            return

        soup = BeautifulSoup(r.text, 'html.parser')

        self.saints_feasts = [
            (f'[{item.a.text}]({item.a["href"]})' if item.a else item.span.text)
            for item in soup.select('[class="ss-result-element"]')
        ]

        self.ready = True
    

    def build_json(self):
        if not self.ready: return []

        return [
            {
                'title':self.title,
                'color':0xA68141, # Golden brown
                'footer':{'text':'Copyright © 2017 Greek Orthodox Archdiocese of America.'},
                'thumbnail':{'url':self.icon_url},
                'author':{
                    'name':'Greek Orthodox Lectionary',
                    'url':self.url
                },
                'fields':[
                    {
                        'name':self.fast[0],
                        'value':self.fast[1],
                        'inline':False
                    },
                    {
                        'name':'Saints & Feasts',
                        'value':'\n'.join([f'• {item}' for item in self.saints_feasts]),
                        'inline':False
                    },
                    {
                        'name':'Scripture Readings',
                        'value':bible_url.html_convert('\n'.join(self.readings)),
                        'inline':False
                    }
                ]
            }
        ]