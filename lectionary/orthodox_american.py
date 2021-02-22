from helpers import bible_url
from helpers import date_expand

from discord import Embed
from bs4 import BeautifulSoup

import requests
import re
import datetime


class OrthodoxAmericanLectionary:
    '''
    Class representing the data scraped from the Orthodox calendar provided by
    the Orthodox Church in America.
    (https://www.oca.org/readings/daily)
    '''

    def __init__(self): self.regenerate()
    
    # Fake data
    def fake_saints_feasts(self): return 'Eve of Theophany . Hieromartyr Theopemptus, Bishop of Nicomedia, and Martyr Theonas (303). Ven. Syncletica of Alexandria (ca. 350). Prophet Micah (9th c. BC). Saint Apollinaria of Egypt (ca. 470). Ven. Phosterius the Hermit (9th c.). Ven. Menas of Sinai (6th c.). Ven. Gregory of Crete (ca. 820). Ven. Romanos, Martyr (1694).'
    def fake_url(self): return 'https://www.oca.org/readings/daily/2021/01/05'
    def fake_readings(self):
        return [
            'Isaiah 35:1-10 (1st Hour, Prophecy)',
            'Acts 13:25-33 (1st Hour, Epistle)',
            'Matthew 3:1-11 (1st Hour, Gospel)',
            'Isaiah 1:16-20 (3rd Hour, Prophecy)',
            'Acts 19:1-8 (3rd Hour, Epistle)',
            'Mark 1:1-8 (3rd Hour, Gospel)',
            'Isaiah 12:3-6 (6th Hour, Prophecy)',
            'Romans 6:3-11 (6th Hour, Epistle)',
            'Mark 1:9-15 (6th Hour, Gospel)',
            'Isaiah 49:8-15 (9th Hour, Prophecy)',
            'Titus 2:11-14; 3:4-7 (9th Hour, Epistle)',
            'Matthew 3:13-17 (9th Hour, Gospel)',
            'Genesis 1:1-13 (Vespers, 1st reading)',
            'Exodus 14:15-18, 21-23, 27-29 (Vespers, 2nd reading)',
            'Exodus 15:22-16:1 (Vespers, 3rd reading)',
            'Joshua 3:7-8, 15-17 (Vespers, 4th reading)',
            '4[2] Kings 2:6-14 (Vespers, 5th reading)',
            '4[2] Kings 5:9-14 (Vespers, 6th reading)',
            'Isaiah 1:16-20 (Vespers, 7th reading)',
            'Genesis 32:1-10 (Vespers, 8th reading)',
            'Exodus 2:5-10 (Vespers, 9th reading)',
            'Judges 6:36-40 (Vespers, 10th reading)',
            '3[1] Kings 18:30-39 (Vespers, 11th reading)',
            '4[2] Kings 2:19-22 (Vespers, 12th reading)',
            'Isaiah 49:8-15 (Vespers, 13th reading)',
            'Hebrews 12:25-26, 13:22-25 (Epistle)',
            'Luke 17:26-37 (Gospel)',
            '1 Corinthians 9:19-27 (Epistle)',
            'Luke 3:1-18 (Gospel)',
            'Isaiah 35:1-10 (Great Blessing of Waters)',
            'Isaiah 55:1-13 (Great Blessing of Waters)',
            'Isaiah 12:3-6 (Great Blessing of Waters)',
            '1 Corinthians 10:1-4 (Great Blessing of Waters, Epistle)',
            'Mark 1:9-11 (Great Blessing of Waters, Gospel)'
        ]


    def clear(self):
        self.today         = None
        self.url           = ''
        self.title         = ''
        self.saints_feasts = []
        self.readings      = []
        self.ready         = False
    

    def regenerate(self):
        self.today = datetime.date.today()
        self.url   = self.today.strftime('https://www.oca.org/readings/daily/%Y/%m/%d')
        self.title = date_expand.expand(self.today)

        try:
            r = requests.get(self.url)
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear()
            return
        
        soup = BeautifulSoup(r.text, 'html.parser')

        # Saints & Feasts
        self.saints_feasts = re.split( # Horrific regex for correct linebreaking
            r'(?<!B\.C\.)(?<! c\.)(?<!Blv\.)(?<!Mt\.)(?<!Rt\.)(?<!St\.)(?<!Ven\.)(?<!ca\.)(?<=\.)\s+',
            soup.select_one('section>p').text.replace('&ldquo;', '"').replace('&rdquo;', '"'))

        # Readings
        pattern = re.compile(r'(?P<composite>Composite [0-9]+ - )?(?P<verses>.*) (\((?P<header>[^,\n]+)(?P<tail>(?:, )(?P<second>.*))?\))')

        readings = []
        for tag in soup.select('section>ul>li>a'):
            try:
                r = requests.get(f'https://www.oca.org{tag["href"]}')
                if r.status_code != 200:
                    self.clear()
                    return
            except:
                self.clear()
                return
            
            soup = BeautifulSoup(r.text, 'html.parser')
            reading = soup.select_one('article>h2').text.strip().replace('\t','').replace('  ',' ')
            
            # Regex to wrap the Bible reference with HTML anchors correctly
            reading = pattern.sub(r'\g<composite><a>\g<verses></a> (\g<header>\g<tail>)', reading)
            
            match     = pattern.match(reading)
            composite = match.group('composite') # Optional
            verses    = match.group('verses')    # Required
            header    = match.group('header')    # Required
            second    = match.group('second')    # Optional

            reading = pattern.sub(r'\g<composite>\g<verses>', reading)
            if second and ('reading' not in second): reading += f' ({second})'

            if readings and readings[-1][0] == header:
                readings[-1][1].append(reading)
            else:
                readings.append([
                    header,
                    [reading]
                ])
        
        self.readings = readings

        self.ready = True
    

    def build_json(self):
        '''
        Helper method to construct a list of Discord Embed json representing
        the calendar data.
        '''
        if not self.ready: return []

        return [
            {
                'title':self.title,
                # Would have used an f-string for the description,
                # but f-string expressions cannot include backslashes
                'description':(
                    self.today.strftime('[**Saints & Feasts**](https://www.oca.org/saints/all-lives/%Y/%m/%d)\n')
                    + "\n".join(self.saints_feasts)
                    + self.today.strftime('\n[**Troparia and Kontakia**](https://www.oca.org/saints/troparia/%Y/%m/%d)')
                    + '\n\n**The Scripture Readings**'
                ),
                'footer':{'text':'Copyright © Orthodox Church in America.'},
                'author':{
                    'name':'American Orthodox Lectionary',
                    'url':self.url
                },
                'fields':[
                    {
                        'name':section[0],
                        'value':bible_url.html_convert('\n'.join(section[1])),
                        'inline':False
                    }
                    for section in self.readings
                ]
            }
        ]