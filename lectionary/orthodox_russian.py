from helpers import bible_url
from helpers import date_expand

from discord import Embed
from bs4 import BeautifulSoup

import requests
import re
import datetime


class OrthodoxRussianLectionary:
    '''
    Class representing the data scraped from the Orthodox calendar provided by
    Holy Trinity Russian Orthodox Church.
    (https://www.holytrinityorthodox.com/calendar/)
    '''

    def __init__(self):
        self.regenerate()
    

    def clear(self):
        self.today     = None
        self.url       = ''
        self.title     = ''
        self.subtitles = []
        self.saints    = []
        self.readings  = []
        self.troparion = []
        self.ready     = False
    

    def regenerate(self):
        '''Function to scrape and store lectionary contents'''
        self.today = datetime.date.today()
        self.url   = 'https://holytrinityorthodox.com/calendar/calendar.php'
        self.url  += f'?month={self.today.month}&today={self.today.day}&year={self.today.year}'
        self.url  += '&dt=1&header=1&lives=1&trp=2&scripture=2'

        try:
            r = requests.get(self.url)
            if r.status_code != 200:
                self.clear_data()
                return
        except:
            self.clear_data()
            return
        
        soup = BeautifulSoup(r.text, 'html.parser')

        # Title & Subtitles
        self.title     = soup.select_one('span[class="dataheader"]').text
        a              = soup.select_one('span[class="headerheader"]').text
        b              = soup.select_one('span[class="headerheader"]>span').text
        self.subtitles = [item for item in [a.replace(b,''), b.strip()] if item]

        # Saints
        self.saints = [
            item
            for item in soup.select_one('span[class="normaltext"]').text.split('\n')
            if item # Rid the list of empty strings
        ]

        # Readings
        readings = soup.select_one('span[class="normaltext"]:nth-child(5)')
        print("test")
        if readings is not NoneType:
            readings = [str(item) for item in readings.contents]
        else:
            readings = [""]
        readings = ''.join(readings)
        readings = readings.replace('\n','').replace('<br/>', '\n')
        if readings[-1] == '\n': readings = readings[:-1]

        # Collapse the Bible links to what's neccesary
        readings = re.sub(r'<a.*>([^<>]*)<\/a>', r'<a>\1</a>', readings)

        # Italize lines that are wrapped in the <em> tag
        readings = re.sub(r'<em>([^<>]*)<\/em>', r'*\1*', readings)
        
        self.readings = readings
        
        # Troparion
        
        # (keys represent saint/tone name)
        keys   = [item.text for item in soup.select('p > b:first-child')]
        values = [item.text for item in soup.select('span[class="normaltext"] > p')]
        values = [value.replace(key, '') for key, value in zip(keys, values)]

        keys   = [key.replace('\n','').replace('\r','').replace(' —','') for key in keys]
        values = [value.replace('\n','').replace('\r','') for value in values]

        self.troparion = {}
        for key, value in zip(keys, values):
            self.troparion[key] = value
        
        self.ready = True
    

    def build_json(self):
        '''
        Public function to construct json representing
        the calendar entry.

        If the data isn't ready, an empty list is returned.
        '''
        if not self.ready: return []

        embeds = []

        # Title & Subtitles
        embeds.append(
            {
                'title':self.title,
                'description':'\n'.join(self.subtitles),
                'author':{
                    'name':'Russian Orthodox Lectionary',
                    'url':self.url
                }
            }
        )

        # Saints & Feasts
        embeds.append(
            {
                'title':'Saints & Feasts',
                'description':'\n'.join(self.saints)
            }
        )
        
        # Readings
        embeds.append(
            {
                'title':'The Scripture Readings',
                'description':bible_url.html_convert(self.readings)
            }
        )

        # Troparion
        embeds.append(
            {
                'title':'Troparion',
                'footer':{'text':'© Holy Trinity Russian Orthodox Church'},
                'fields':[
                    {
                        'name':saint,
                        'value':self.troparion[saint],
                        'inline':False
                    }
                    for saint in self.troparion
                ]
            }
        )

        return embeds