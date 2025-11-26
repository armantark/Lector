from helpers import bible_url, date_expand
from helpers.bible_reference import normalize_coptic_reference
from lectionary.base import Lectionary


class OrthodoxCopticLectionary(Lectionary):
    """
    Class representing the data scraped from the Orthodox calendar provided by
    St. Mark's Coptic Orthodox Church
    (https://copticchurch.net/readings)
    """

    @staticmethod
    def clean_reference(string):
        """
        Normalize a Bible reference using the shared Coptic reference helper.
        """
        return normalize_coptic_reference(string)

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

        # Define the titles and corresponding indices
        liturgy_parts = [
            ('Pauline Epistle', 0),
            ('Catholic Epistle', 1),
            ('Acts of the Apostles', 2),
            ('Psalm', 3),
            ('Gospel', 4)
        ]

        # Iterate through the liturgy parts and append to value if index exists
        for title, index in liturgy_parts:
            if len(links) > index:
                if index == 3:
                    # Add Synaxarium
                    liturgy_data['value'] += 'Synaxarium:\n'
                    liturgy_data['value'] += '\n'.join([f'• {item}' for item in self.synaxarium]) + '\n'
                liturgy_data['value'] += f'{title}: {links[index]}\n'

        return liturgy_data
