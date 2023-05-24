import datetime
import re

import requests
from bs4 import BeautifulSoup

from helpers import bible_url
from helpers import date_expand


class OrthodoxAmericanLectionary:
    """
    Class representing the data scraped from the Orthodox calendar provided by
    the Orthodox Church in America.
    (https://www.oca.org/readings/daily)
    """

    def __init__(self):
        self.today = None
        self.url = None
        self.title = None
        self.saints_feasts = None
        self.readings = None
        self.ready = None
        self.today = None
        self.url = None
        self.title = None
        self.saints_feasts = None
        self.readings = None
        self.ready = None
        self.regenerate()

    def clear(self):
        self.today = None
        self.url = ''
        self.title = ''
        self.saints_feasts = []
        self.readings = []
        self.ready = False

    def regenerate(self):
        self.today = datetime.date.today()
        self.url = self.today.strftime('https://www.oca.org/readings/daily/%Y/%m/%d')
        self.title = date_expand.expand(self.today)

        try:
            r = requests.get(self.url)
            if r.status_code != 200:
                self.clear()
                return None
        except requests.RequestException:
            self.clear()
            return
        soup = BeautifulSoup(r.text, 'html.parser')

        # Saints & Feasts
        self.saints_feasts = re.split(  # Horrific regex for correct linebreaking
            r'(?<!B\.C\.)(?<! c\.)(?<!Blv\.)(?<!Mt\.)(?<!Rt\.)(?<!St\.)(?<!Ven\.)(?<!ca\.)(?<=\.)\s+',
            soup.select_one('section>p').text.replace('&ldquo;', '"').replace('&rdquo;', '"'))

        # Readings
        pattern = re.compile(
            r'(?P<composite>Composite [0-9]+ - )?(?P<verses>.*) '
            r'(\((?P<header>[^,\n]+)(?P<tail>, (?P<second>.*))?\))')

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
            reading = soup.select_one('article>h2').text.strip().replace('\t', '').replace('  ', ' ')

            # Regex to wrap the Bible reference with HTML anchors correctly
            reading = pattern.sub(r'\g<composite><a>\g<verses></a> (\g<header>\g<tail>)', reading)

            match = pattern.match(reading)
            header = match.group('header')  # Required
            second = match.group('second')  # Optional

            reading = pattern.sub(r'\g<composite>\g<verses>', reading)
            if second and ('reading' not in second):
                reading += f' ({second})'

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
        """
        Helper method to construct a list of Discord Embed json representing
        the calendar data.
        """
        if not self.ready:
            return []

        return [
            {
                'title': self.title,
                # Would have used an f-string for the description,
                # but f-string expressions cannot include backslashes
                'description': (
                        self.today.strftime('[**Saints & Feasts**](https://www.oca.org/saints/all-lives/%Y/%m/%d)\n')
                        + "\n".join(self.saints_feasts)
                        + self.today.strftime(
                    '\n[**Troparia and Kontakia**](https://www.oca.org/saints/troparia/%Y/%m/%d)')
                        + '\n\n**The Scripture Readings**'
                ),
                'footer': {'text': 'Copyright © Orthodox Church in America.'},
                'author': {
                    'name': 'American Orthodox Lectionary',
                    'url': self.url
                },
                'fields': [
                    {
                        'name': section[0],
                        'value': bible_url.html_convert('\n'.join(section[1])),
                        'inline': False
                    }
                    for section in self.readings
                ]
            }
        ]
