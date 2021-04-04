from helpers import bible_url
from helpers import date_expand

from discord import Embed

from bs4 import BeautifulSoup

import requests
import datetime


class ArmenianLectionary:
    def __init__(self): self.regenerate()
    

    def clear(self):
        self.today       = None
        self.url         = ''
        self.title       = ''
        self.description = ''
        self.readings    = []

        self.synaxarium  = '' # Url

        self.ready       = False


    def get_synaxarium(self):
        '''
        Get the daily synaxarium (and implicit color)
        '''
        url = self.today.strftime(f'https://www.qahana.am/en/holidays/%Y-%m-%d/1')

        try:
            r = requests.get(url, headers={'User-Agent': ''})
            if r.status_code != 200:
                return ''
        except:
            return ''
        
        soup = BeautifulSoup(r.text, 'html.parser')

        if soup.select_one('div[class^="holidayItem"]>h2'):
            return url
        else:
            return ''


    def regenerate(self):
        self.today = datetime.date.today()
        self.url   = self.today.strftime(f'https://vemkar.us/%Y/%m/%d/%B-{self.today.day}-%Y')
        
        try:
            r = requests.get(self.url)
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear()
            return
        
        soup = BeautifulSoup(r.text, 'html.parser')

        self.title    = soup.select('h2')[1].text
        self.subtitle = date_expand.auto_expand(self.today, self.title)
        readings = []

        readings_raw_select = soup.select('h4[style]')

        for reading in readings_raw_select:
            readings += reading.text

        print(self.title)

        substitutions = {'III ':'3 ','II ':'2 ','I ':'1 ','Azariah':'Prayer of Azariah'}
        for original in substitutions.keys():
            readings = readings.replace(original, substitutions[original])
        
        if readings == '[No readings for this day]':
            self.readings = [readings]
        else:
            self.readings = readings.split('\n')

        # Get pages with additional lectionary notes, if they exist
        try:
            r = requests.get(self.today.strftime(f'https://vemkar.us/%B-{self.today.day}-%Y'))
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear()
            return
        
        # If there was no redirect, this is a unique resource
        if (len(r.history) == 0):
            soup = BeautifulSoup(r.text, 'html.parser')
            self.notes_url = soup.select_one("p[class='attachment']>a")['href']
        # If there was a redirect, everything was already scraped
        else:
            self.notes_url = ''

        self.synaxarium = self.get_synaxarium()

        self.ready = True


    def build_json(self):
        if not self.ready: return []

        return [
            {
                'title':self.title + '\n' + self.subtitle,
                'color':(
                    0xca0000
                    if self.synaxarium != ''
                    else 0x202225
                ),
                'description':(
                    (
                        f'[Synaxarium]({self.synaxarium})\n\n'
                        if self.synaxarium != ''
                        else ''
                    ) +
                    '\n'.join(
                        [
                            (
                                bible_url.convert(reading)
                                if reading != '[No readings for this day]'
                                else reading
                            )
                            for reading in self.readings
                        ]
                    ) + (
                        f"\n\n*[Notes]({self.notes_url})"
                        if self.notes_url
                        else ''
                    )
                ),
                'footer':{'text':'Copyright © VEMKAR.'},
                'author':{
                    'name':'Armenian Lectionary',
                    'url':self.url
                }
            }
        ]