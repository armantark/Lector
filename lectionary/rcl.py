from helpers import bible_url
from helpers import date_expand

from bs4 import BeautifulSoup
from discord import Embed

import requests
import re
import datetime


class RevisedCommonLectionary:
    def __init__(self):
        self.regenerate()
    

    def clear(self):
        self.today    = None
        self.url      = ''
        self.title    = ''
        self.sections = {}
        self.color    = None
        self.ready    = False


    def _explode_reference_list(self, text):
        '''
        This helper method takes in a common-separated list of Bible
        references, and explodes it into a list where each reference
        is independent
        
        For instance, 'John 1; Acts 7; 8' will get exploded to
        ['John 1', 'Acts 7', 'Acts 8']
        '''
        text = re.sub(
            r'(([0-9] )?[a-zA-Z]+[0-9 \-\:]+); ([0-9]+[^ ])',
            r'\1<semicolon> \3',
            text)
        
        return [
            item.replace('<semicolon>', ';')
            for item in text.split('; ')]


    def regenerate(self):
        self.url = 'https://lectionary.library.vanderbilt.edu/daily.php'
        
        try:
            r = requests.get(self.url)
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear()
            return

        self.today = datetime.date.today()
        soup = BeautifulSoup(r.text, 'html.parser')

        self.title  = f'Daily Readings for {date_expand.expand(self.today)}'
        self.title += f' (Year {soup.select_one("[id=main_text]>h2").text[-1]})'

        lines = soup.select('ul[class="daily_day"]>li')

        # Generate the regex pattern matching today's date
        check = self.today.strftime(f'%B.* {self.today.day}[^0-9].*%Y')
        
        self.sections = {}
        got_today = False
        for line in lines:
            line = [str(item) for item in line.contents]
            line = ''.join(line).replace('&amp;','&')

            # If the entry is not for today
            if not re.search(check, line):
                if got_today: break
                continue
            got_today = True

            # Listings with explicit list of readings
            match = re.search(r'<strong>(.*)<\/strong>: *<a href="http:.*>(.*)<\/a>', line)
            if match:
                readings = self._explode_reference_list(match.group(2))
                readings = '\n'.join([f'<a>{reading}</a>' for reading in readings])
                self.sections[''] = readings
                break
                
            # Listings with semi-continuous & complementary 
            match = re.search(r'<strong>(.*)<\/strong>: <br\/>Semi-continuous: <a.*>(.*)<\/a><br\/>Complementary: <a.*>(.*)<\/a>', line)
            if match:
                self.sections['Semi-continuous'] = '\n'.join([
                    f'<a>{reading}</a>'
                    for reading in self._explode_reference_list(match.group(2))
                ])
            
                self.sections['Complementary'] = '\n'.join([
                    f'<a>{reading}</a>'
                    for reading in self._explode_reference_list(match.group(3))
                ])

                break
                
            # Listings that link to another page for the readings
            match = re.search(r'<strong>(.*)<\/strong>: *<strong><a href="(.*)">(.*)<\/a><\/strong>', line)
            if match:
                fetched = self._scrape_text_php(f'https://lectionary.library.vanderbilt.edu/{match.group(2)}')
                if (fetched == []):
                    self.clear()
                    return
                else:
                    self.sections[match[3]] = fetched

        self.color = self._get_color()

        self.ready = True
    

    def _scrape_text_php(self, url):
        '''
        Instead of providing a list of references, the daily readings page
        might link to another page containing a list of readings. This
        helper method scrapes from that.
        '''
        try:
            r = requests.get(url)
            if r.status_code != 200: return []
        except:
            return []

        soup = BeautifulSoup(r.text, 'html.parser')

        readings = soup.select_one('div[class="texts_msg_bar"]:first-child>ul')
        readings = readings.text.replace('\n','')

        links = readings.replace(' and ',';').replace(' or ',';').replace('\xa0\xa0•\xa0', ';').split(';')

        for link in links:
            readings = readings.replace(link, f'<a>{link}</a>')
        
        readings = readings.replace('\xa0\xa0•\xa0', '\n')

        return readings
    

    def _get_color(self):
        '''
        Helper method to fetch today's liturgical color.
        On success, a color int will be returned.
        On failure, None will be returned.
        '''
        colors = {
            'green':25600,
            'red':9830424, # Carmine
            'purple':8388736,
            'black':0,
            'white':16777215
        }

        url = self.today.strftime('https://liturgical.today/reformed/%Y-%m-%d')

        try:
            r = requests.get(url=url)
            if r.status_code != 200:
                return 0
        except:
            return 0
        
        color = r.text.replace('"','').replace('[','').replace(']','').split(', ')[1]

        if color in colors: return colors[color]
        else: return 0
        

    def build_json(self):
        '''
        Convert daily calendar info to discord Embed json data
        '''
        if not self.ready: return []

        return [
            {
                'title':self.title,
                'description':(
                    bible_url.html_convert(self.sections[''])
                    if '' in self.sections
                    else ''
                ),
                'color':self.color,
                'footer':{'text':'Revised Common Lectionary, Copyright © 1992 Consultation on Common Texts. Used by permission.'},
                'author':{
                    'name':'Revised Common Lectionary',
                    'url':self.url
                },
                'fields':[
                    {
                        'name':key,
                        'value':bible_url.html_convert(self.sections[key]),
                        'inline':False
                    }
                    for key in self.sections if key
                ]
            }
        ]