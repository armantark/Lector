from helpers import bible_url
from helpers import date_expand

from discord import Embed
from bs4 import BeautifulSoup

import requests
import datetime


class OrthodoxCopticLectionary:
    '''
    Class representing the data scraped from the Orthodox calendar provided by
    St. Mark's Coptic Orthodox Church
    (https://copticchurch.net/readings)
    '''

    def __init__(self): self.regenerate()


    def clear(self):
        self.today      = None
        self.url        = ''
        self.title      = ''
        self.subtitle   = ''
        self.readings   = []
        self.synaxarium = []
        self.ready      = False


    def clean_reference(self, string):
        '''
        Function to clean a Bible reference so it's ready for the url converter
        '''
        replacements = {
            '  & ':'; ',
            ' - ':'-',
            'Matt ':'Matthew ',
            'Mk ':'Mark ',
            'Lk ':'Luke ',
            # John moved for correct replacement

            'Rom ':'Romans ',

            '1Cor ':'1 Corinthians ',
            '2Cor ':'2 Corinthians ',
            '1Corinthians ':'1 Corinthians ',
            '2Corinthians ':'2 Corinthians ',

            'Col ':'Colossians ',

            'Heb ':'Hebrews ',

            '1Pet ':'1 Peter ',
            '1Peter ':'1 Peter ',

            '2Pet ':'2 Peter ',
            '2Peter ':'2 Peter ',

            '1Jn ':'1 John ',
            '2Jn ':'2 John ',
            '3Jn ':'3 John ',

            '1John ':'1 John ',
            '2John ':'2 John ',
            '3John ':'3 John ',

            'Jn ':'John '
        }

        for item in replacements:
            string = string.replace(item, replacements[item])

        return string


    def regenerate(self):
        self.today = datetime.date.today()
        self.url   = self.today.strftime('https://copticchurch.net/readings??g_year=%Y&g_month=%m&g_day=%d')
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

        self.subtitle = soup.select_one('h2').text

        self.readings = [
            self.clean_reference(item.text)
            for item in soup.select('h5')]

        self.synaxarium = [
            f'[{tag.text}](https://copticchurch.net{tag["href"]})'
            for tag in soup.select('a[href^="/synaxarium/"]')
        ]

        self.ready = True


    def build_json(self):
        if not self.ready: return []

        links = [bible_url.convert(reading) for reading in self.readings]

        # print(links)
        # print(len(links))
        final = [{
                    'title':self.title,
                    'description':self.subtitle,
                    'color':0xF2DB87,
                    'footer':{'text':'Copyright © St. Mark\'s Coptic Orthodox Church, Jersey City, NJ.'},
                    'author':{
                        'name':'Coptic Orthodox Lectionary',
                        'url':self.url
                    },
                    'fields':[{'name':'','value':f'{'See website for more info': self.url}'}]
                }]
        if len(links) == 0:
            return final
        elif len(links) > 7:
            # if there are Vespers
            final[0]['fields'] = [
                        {
                            'name':'Vespers',
                            'value':f'Psalm: {links[0]}\nGospel: {links[1]}'
                        },
                        {
                            'name':'Matins',
                            'value':f'Psalm: {links[2]}\nGospel: {links[3]}'
                        },
                        {
                            'name':'Liturgy',
                            'value':(
                                f'Pauline Epistle: {links[4]}\n'                       +
                                f'Catholic Epistle: {links[5]}\n'                      +
                                f'Acts of the Apostles: {links[6]}\n'                  +
                                f'Synaxarium:\n'                                       +
                                '\n'.join([f'• {item}' for item in self.synaxarium]) +
                                '\n'                                                   +
                                f'Psalm: {links[7]}\n'                                 +
                                f'Gospel: {links[8]}'
                            ),
                            'inline':False
                        }
                    ]
        else:
            # if there are no Vespers. This seems to only happen during the Nineveh fast.
            final[0]['fields'] = [
                        {
                            'name':'Matins',
                            'value':f'Psalm: {links[0]}\nGospel: {links[1]}'
                        },
                        {
                            'name':'Liturgy',
                            'value':(
                                f'Pauline Epistle: {links[2]}\n'                       +
                                f'Catholic Epistle: {links[3]}\n'                      +
                                f'Acts of the Apostles: {links[4]}\n'                  +
                                f'Synaxarium:\n'                                       +
                                '\n'.join([f'• {item}' for item in self.synaxarium]) +
                                '\n'                                                   +
                                f'Psalm: {links[5]}\n'                                 +
                                f'Gospel: {links[6]}'
                            ),
                            'inline':False
                        }
                    ]
        return final
