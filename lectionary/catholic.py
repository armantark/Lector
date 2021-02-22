from helpers import bible_url
from helpers import date_expand

from bs4 import BeautifulSoup
from discord import Embed

import requests
import re
import datetime


class CatholicPage:
    '''
    A class that takes in the link, and possibly the raw HTML, for a Catholic
    readings page, scrapes the key info, and uses this as its attributes
    '''

    def __init__(self, today, url, source_text=None):
        self.today = today
        self.url   = url

        if source_text is None:
            try:
                r = requests.get(url)
                if r.status_code != 200:
                    self.clear()
                    return
            except:
                self.clear()
                return
            
            source_text = r.text

        soup = BeautifulSoup(source_text, 'html.parser')

        self.title  = soup.title.text.replace(' | USCCB','')
        self.footer = soup.select_one('h2 ~ p').text.strip()

        self.desc = date_expand.auto_expand(self.today, self.title)

        blocks = soup.select('.b-verse>div>div>div>div')
        self.sections = {}
        
        for block in blocks:
            header = block.select_one('h3').text.strip()

            if (header == ''): header = 'Gospel'
            # There is a glitch on the website where the 'Gospel' label
            # will be missing from the page. None of the other labels
            # appear to do that for whatever reason. It cannot be left
            # empty because Discord embed field names must be non-empty.

            lines = []
            for link in block.select('a'):
                link = link.text.strip().title()
                if link == '': continue
                link = link.replace('.','').replace(u'\xa0',u' ')
                link = link.replace(' And ',', ')
                
                # If a reference in the Responsorial Psalm section does not
                # include "Ps", insert it at the beginning
                if (header == 'Responsorial Psalm') and (link[0] in list('0123456789')) and (link[:2] not in ['1 ','2 ','3 ']):
                    link = 'Ps ' + link

                lines.append(link)
            
            if len(lines) > 0:
                for index, link in enumerate(lines):

                    case0 = re.search(r'(.*) \(cited in (.*)\)', lines[index])
                    if case0:
                        # Deals with cases that look like "Isaiah 61:1 (cited in Luke 4:18)"
                        first  = self._clean_ref(case0.group(1))
                        second = self._clean_ref(case0.group(2))
                        lines[index] = f'<a>{first}</a> (cited in <a>{second}</a>)'
                        continue
                    
                    pattern = re.compile(r'((?:1 |2 |3 )?[a-zA-Z]+) ([0-9 ,:-]+) Or ([0-9: ,-]+)')
                    case1 = re.search(pattern, lines[index])
                    if case1:
                        first = self._clean_ref(re.sub(pattern, r'\1 \2', lines[index]))
                        second = self._clean_ref(re.sub(pattern, r'\1 \3', lines[index]))
                        lines[index] = f'<a>{first}</a> or <a>{second}</a>'
                        continue

                    if link.startswith('See '):
                        new = lines[index][4:]
                        lines[index] = f'See <a>{self._clean_ref(new)}</a>'
                    elif link.startswith('Cf '):
                        new = lines[index][3:]
                        lines[index] = f'Cf. <a>{self._clean_ref(new)}</a>'
                    else:
                        lines[index] = f'<a>{self._clean_ref(lines[index])}</a>'
                    
                lines = ' or\n'.join(lines)
                self.sections[header] = lines
        
        self.ready = True


    def clear(self):
        self.url      = ''
        self.title    = ''
        self.desc     = ''
        self.sections = {}
        self.footer   = ''
        self.ready    = False


    def _clean_ref(self, reference):
        substitutions = {
            'GN'     : 'Genesis',
            'EX'     : 'Exodus',
            'LV'     : 'Leviticus',
            'NM'     : 'Numbers',

            'JDT'    : 'Judith', # This gets moved up so the proper substitution is made
            'DT'     : 'Deuteronomy',

            'JOS'    : 'Joshua',
            'JGS'    : 'Judges',
            'RU'     : 'Ruth',
            '1 SM'   : '1 Samuel',
            '2 SM'   : '2 Samuel',
            '1 KGS'  : '1 Kings',
            '2 KGS'  : '2 Kings',
            '1 CHR'  : '1 Chronicles',
            '2 CHR'  : '2 Chronicles',
            'EZR'    : 'Ezra',
            'NEH'    : 'Nehemiah',

            'TB'     : 'Tobit',
            #           Judith
            'EST'    : 'Esther',
            '1 MC'   : '1 Maccabees',
            '2 MC'   : '2 Maccabees',

            'JB'     : 'Job',
            'PS'     : 'Psalm',
            'PRV'    : 'Proverbs',
            'ECCL'   : 'Ecclesiastes',
            'SGS'    : 'Song of Songs',
            'WIS'    : 'Wisdom',
            'SIR'    : 'Sirach',

            'IS'     : 'Isaiah',
            'JER'    : 'Jeremiah',
            'LAM'    : 'Lamentations',
            'BAR'    : 'Baruch',
            'EZ'     : 'Ezekiel',
            'DN'     : 'Daniel',
            'HOS'    : 'Hosea',
            'JL'     : 'Joel',
            'AM'     : 'Amos',
            'OB'     : 'Obadiah',
            'JON'    : 'Jonah',
            'MI'     : 'Micah',
            'NA'     : 'Nahum',
            'HB'     : 'Habakkuk',
            'ZEP'    : 'Zephaniah',
            'HG'     : 'Haggai',
            'ZEC'    : 'Zachariah',
            'MAL'    : 'Malachi',

            'MT'     : 'Matthew',
            'MK'     : 'Mark',
            'LK'     : 'Luke',
            'JN'     : 'John',

            'ACTS'   : 'Acts',

            'ROM'    : 'Romans',
            '1 COR'  : '1 Corinthians',
            '2 COR'  : '2 Corinthians',
            'GAL'    : 'Galatians',
            'EPH'    : 'Ephesians',
            'PHIL'   : 'Philippians',
            'COL'    : 'Colossians',
            '1 THES' : '1 Thessalonians',
            '2 THES' : '2 Thessalonians',
            '1 TM'   : '1 Timothy',
            '2 TM'   : '2 Timothy',
            'TI'     : 'Titus',
            'PHLM'   : 'Philemon',
            'HEB'    : 'Hebrews',

            'JAS'    : 'James',
            '1 PT'   : '1 Peter',
            '2 PT'   : '2 Peter',
            '1 JN'   : '1 John',
            '2 JN'   : '2 John',
            '3 JN'   : '3 John',
            'JUDE'   : 'Jude',
            'RV'     : 'Revelation'
        }

        reference = reference.upper()
        for original in substitutions.keys():
            if f'{original} ' in reference:
                reference = reference.replace(original, substitutions[original])
                break
        return reference.title()


class CatholicLectionary:
    def __init__(self):
        self.regenerate()
    

    def clear(self):
        self.today = None
        self.color = 0
        self.pages = []
        self.ready = False


    def get_color(self):
        '''
        Get the day's liturgical color as an integer
        '''
        default = 0x000000

        try:
            r = requests.get('https://bible.usccb.org/')
            if r.status_code != 200:
                return default
        except:
            return default
        
        soup = BeautifulSoup(r.text, 'html.parser')
        tags = soup.select(self.today.strftime('a[href^="/bible/readings/%m%d%y"]'))
        color = [tag['data-colors'] for tag in tags if tag['data-colors'] != ''][0]

        if color is not None:
            return {
                'red':0xEE4540,
                'green':0x03AA5D,
                'white':0xFFFFFE, # Pure white doesn't work :/
                'violet':0x9059AA,
                'pink':0xF9539F
            }.get(color, default)
        else:
            return default


    def regenerate(self):
        '''
        Helper method that handles all the GET requests that are needed to get
        the pages that contain the appropriate lectionary info.
        '''
        self.today = datetime.date.today()
        permalink = self.today.strftime('https://bible.usccb.org/bible/readings/%m%d%y.cfm')

        try:
            r = requests.get(permalink)
            if r.status_code != 200:
                self.clear()
                return
        except:
            self.clear_data()
            return

        soup = BeautifulSoup(r.text, 'html.parser')
        blocks = soup.select('.b-verse>div>div>div>div')

        # If the daily page has readings
        if len(blocks) > 1:
            page = CatholicPage(self.today, permalink, r.text)
            if page.ready:
                self.pages = [page]
            else:
                self.clear()
                return

        # Check if the daily page has links to other pages with readings.
        # Each page gets its own embed.
        links = []
        for link in re.findall(r'\/bible\/readings\/[0-9]{4}[a-z-]+\.cfm', r.text):
            links.append(link)

        for link in links:
            # If the link is relative, make it absolute
            if 'https://' != link[:8]: link = ''.join(['https://bible.usccb.org', link])

            page = CatholicPage(self.today, link)
            if page.ready: self.pages.append(page)
            else:
                self.clear()
                return
        
        # Get and store the liturgical color
        self.color = self.get_color()

        self.ready = True


    def build_json(self):
        '''
        Helper method to construct a list of Discord embed json based on
        the data scraped from the daily readings webpages
        '''
        if not self.ready: return []

        embeds = []

        # For each page that was scraped
        for page in self.pages:
            embeds.append(
                {
                    'title':page.title,
                    'description':page.desc,
                    'color':self.color,
                    'footer':{'text':page.footer+'\nCopyright © USCCB.'},
                    'author':{
                        'name':'Catholic Lectionary',
                        'url':page.url
                    },
                    'fields':[
                        {
                            'name':header,
                            'value':bible_url.html_convert(page.sections[header]),
                            'inline':False
                        }
                        # For each lectionary section on the page
                        # Ex: Reading 1, Responsorial Psalm, Reading 2, Alleluia, Gospel
                        for header in page.sections
                    ]
                }
            )

        return embeds