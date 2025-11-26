import re

from helpers import bible_url, date_expand
from lectionary.base import Lectionary


class OrthodoxAmericanLectionary(Lectionary):
    def __init__(self):
        super().__init__()
        self.regenerate()

    def regenerate(self):
        super().regenerate()
        self.url = self.today.strftime('https://www.oca.org/readings/daily/%Y/%m/%d')
        self.extract_title(None)

        soup = self.fetch_and_parse_html(self.url)
        if not soup:
            return

        self.extract_synaxarium(soup)
        self.extract_readings(soup)

        self.ready = True

    def extract_synaxarium(self, soup):
        self.synaxarium = re.split(
            r'(?<!B\.C\.)(?<! c\.)(?<!Blv\.)(?<!Mt\.)(?<!Rt\.)(?<!St\.)(?<!Ven\.)(?<!ca\.)(?<=\.)\s+',
            soup.select_one('section>p').text.replace('&ldquo;', '"').replace('&rdquo;', '"'))

    def extract_readings(self, soup):
        pattern = re.compile(
            r'(?P<composite>Composite [0-9]+ - )?(?P<verses>.*) '
            r'(\((?P<header>[^,\n]+)(?P<tail>, (?P<second>.*))?\))')

        readings = []
        for tag in soup.select('section>ul>li>a'):
            soup = self.fetch_and_parse_html(f'https://www.oca.org{tag["href"]}')
            if not soup:
                return

            reading = soup.select_one('article>h2').text.strip().replace('\t', '').replace('  ', ' ')
            reading = pattern.sub(r'\g<composite><a>\g<verses></a> (\g<header>\g<tail>)', reading)

            match = pattern.match(reading)
            header = match.group('header')
            second = match.group('second')

            reading = pattern.sub(r'\g<composite>\g<verses>', reading)
            if second and ('reading' not in second):
                reading += f' ({second})'

            if readings and readings[-1][0] == header:
                readings[-1][1].append(reading)
            else:
                readings.append([header, [reading]])

        self.readings = readings

    def extract_title(self, soup):
        self.title = date_expand.expand(self.today)

    def extract_subtitle(self, soup):
        # Not required in this class as no subtitle is extracted
        pass

    def build_json(self):
        if not self.ready:
            return []

        return [
            {
                'title': self.title,
                'description': self.build_description(),
                'footer': {'text': 'Source: oca.org'},
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

    def build_description(self):
        return (
                self.today.strftime('[**Saints & Feasts**](https://www.oca.org/saints/all-lives/%Y/%m/%d)\n')
                + "\n".join(self.synaxarium)
                + self.today.strftime(
            '\n[**Troparia and Kontakia**](https://www.oca.org/saints/troparia/%Y/%m/%d)')
                + '\n\n**The Scripture Readings**'
        )
