from helpers import bible_url, date_expand
from lectionary.lectionary import Lectionary


class OrthodoxCopticLectionary(Lectionary):
    """
    Class representing the data scraped from the Orthodox calendar provided by
    St. Mark's Coptic Orthodox Church
    (https://copticchurch.net/readings)
    """

    @staticmethod
    def clean_reference(string):
        """
        Function to clean a Bible reference, so it's ready for the url converter
        """
        replacements = {
            '  & ': '; ',
            ' - ': '-',
            'Matt ': 'Matthew ',
            'Mk ': 'Mark ',
            'Lk ': 'Luke ',
            'Rom ': 'Romans ',
            '1Cor ': '1 Corinthians ',
            '2Cor ': '2 Corinthians ',
            '1Corinthians ': '1 Corinthians ',
            '2Corinthians ': '2 Corinthians ',
            'Col ': 'Colossians ',
            'Heb ': 'Hebrews ',
            '1Pet ': '1 Peter ',
            '1Peter ': '1 Peter ',
            '2Pet ': '2 Peter ',
            '2Peter ': '2 Peter ',
            '1Jn ': '1 John ',
            '2Jn ': '2 John ',
            '3Jn ': '3 John ',
            '1John ': '1 John ',
            '2John ': '2 John ',
            '3John ': '3 John ',
            'Jn ': 'John '
        }

        for item in replacements:
            string = string.replace(item, replacements[item])

        return string

    def regenerate(self):
        super().regenerate()
        self.url = self.today.strftime('https://copticchurch.net/readings??g_year=%Y&g_month=%m&g_day=%d')

        soup = self.fetch_and_parse_html(self.url)
        if not soup:
            return

        self.extract_title(soup)
        self.extract_subtitle(soup)
        self.extract_readings(soup)
        self.extract_synaxarium(soup)

        self.ready = True

    def extract_subtitle(self, soup):
        self.subtitle = soup.select_one('h2').text

    def extract_readings(self, soup):
        self.readings = [
            self.clean_reference(item.text)
            for item in soup.select('h5')
        ]

    def extract_synaxarium(self, soup):
        self.synaxarium = [
            f'[{tag.text}](https://copticchurch.net{tag["href"]})'
            for tag in soup.select('a[href^="/synaxarium/"]')
        ]

    def extract_title(self, soup):
        self.title = date_expand.expand(self.today)

    def build_json(self):
        if not self.ready:
            return []

        links = [bible_url.convert(reading) for reading in self.readings]
        final = [self.build_base_json()]

        if len(links) == 0:
            return final
        elif len(links) > 7:
            final[0]['fields'] = self.build_vespers_json(links)
        else:
            final[0]['fields'] = self.build_no_vespers_json(links)

        return final

    def build_base_json(self):
        return {
            'title': self.title,
            'description': self.subtitle,
            'color': 0xF2DB87,
            'footer': {'text': 'Copyright © St. Mark\'s Coptic Orthodox Church, Jersey City, NJ.'},
            'author': {
                'name': 'Coptic Orthodox Lectionary',
                'url': self.url
            },
            'fields': [{'name': 'See website for more information', 'value': f'[CopticChurch.net]({self.url})'}]
        }

    def build_vespers_json(self, links):
        return [
            {
                'name': 'Vespers',
                'value': f'Psalm: {links[0]}\nGospel: {links[1]}'
            },
            {
                'name': 'Matins',
                'value': f'Psalm: {links[2]}\nGospel: {links[3]}'
            },
            self.build_liturgy_json(links[4:])
        ]

    def build_no_vespers_json(self, links):
        return [
            {
                'name': 'Matins',
                'value': f'Psalm: {links[0]}\nGospel: {links[1]}'
            },
            self.build_liturgy_json(links[2:])
        ]

    def build_liturgy_json(self, links):
        liturgy_data = {
            'name': 'Liturgy',
            'value': '',
            'inline': False
        }

        # Check each index before accessing it in the links list
        if len(links) > 0:
            liturgy_data['value'] += f'Pauline Epistle: {links[0]}\n'
        if len(links) > 1:
            liturgy_data['value'] += f'Catholic Epistle: {links[1]}\n'
        if len(links) > 2:
            liturgy_data['value'] += f'Acts of the Apostles: {links[2]}\n'

        liturgy_data['value'] += f'Synaxarium:\n'
        liturgy_data['value'] += '\n'.join([f'• {item}' for item in self.synaxarium]) + '\n'

        if len(links) > 3:
            liturgy_data['value'] += f'Psalm: {links[3]}\n'
        if len(links) > 4:
            liturgy_data['value'] += f'Gospel: {links[4]}'

        return liturgy_data
