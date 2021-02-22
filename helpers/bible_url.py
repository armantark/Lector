import re


def convert(reference):
    '''
    Converts an individual Bible reference into a neat Markdown link
    '''

    # There's a weird nuance with how BibleGateway fetches Psalm 151.
    # Even when you're using a translation that includes it, the term
    # "Psalm 151" throws a "No Results Found" Error unless you write it
    # with a pseudo-chapter number: "Psalm 151 1".
    replacements = {
        'Psalm 151':'Psalm 151 1',
        'St. Paul\'s Letter to the ':'',
        'St. Paul\'s Letter to ':'',
        'St. Paul\'s First Letter to the ':'1 ',
        'St. Paul\'s Second Letter to the ':'2 ',
        'St. Paul\'s First Letter to ':'1 ',
        'St. Paul\'s Second Letter to ':'2 ',
        'St. James\' Universal Letter': 'James',
        'St. Peter\'s First Universal Letter':'1 Peter',
        'St. Peter\'s Second Universal Letter':'2 Peter'
    }

    for item in replacements:
        reference = reference.replace(item, replacements[item])

    anchor = reference

    # Clean up references that have alternative chapter numbers within
    # brackets so the links don't break
    # Ex: '4[2] Kings 2:6-14' => '2 Kings 2:6-14'
    reference = re.sub(r'([0-9]+\[([0-9]+)\])', r'\2', reference)

    # Get rid of letter subreferences in verses
    pattern   = re.compile(r'([0-9]+)([a-zA-Z]+)')

    # '1 Samuel 2:8ABCD' => '1 Samuel 2:8'
    reference = re.sub(pattern, r'\1', reference)
    
    # '1 Samuel 2:8ABCD' => '1 Samuel 2:8abcd'
    for item in re.findall(pattern, anchor):
        item = ''.join(item)
        anchor = anchor.replace(item, item.lower())
    
    reference = shorten(reference).replace(' ', '+')
    return f'[{anchor}](https://biblegateway.com/passage/?search={reference})'


def html_convert(text):
    '''
    Converts a string with anchored Bible references to Markdown

    In: "God creates everything\nin <a>Genesis 1:1</a>"
    Out: "God creates everything\nin [Genesis 1:1](https://www.example.com)"
    '''
    for match in re.findall(r'(<a>([^<>]*)<\/a>)', text):
        text = text.replace(match[0], convert(match[1]))
    
    return text


def shorten(text):
    '''
    Given a Bible reference, shortens it for linking efficiency
    NOTE: These are optimized for BibleGateway.com
    '''

    text = text.replace(', ',',').replace('; ',';').title()

    abbreviations = {
        # Old Testament
        'Genesis':'Ge',
        'Exodus':'Ex',
        'Leviticus':'Lv',
        'Numbers':'Nm',
        'Deuteronomy':'Dt',
        'Joshua':'Jsh',
        'Judges':'Jg',
        'Ruth':'Ru',
        '1 Samuel':'1Sa',
        '2 Samuel':'2Sa',
        '1 Kings':'1Ki',
        '2 Kings':'2Ki',
        '1 Chronicles':'1Ch',
        '2 Chronicles':'2Ch',
        'Ezra':'Ezr',
        'Nehemiah':'Ne',
        'Esther':'Est',
        'Job':'Jb',
        'Psalms':'Ps',
        'Psalm':'Ps',
        'Proverbs':'Pr',
        'Ecclesiastes':'Ec',

        'Song Of Solomon':'SS',
        'Song Of Songs':'SS',

        'Isaiah':'Is',
        'Jeremiah':'Jr',
        'Lametations':'La',
        'Ezekiel':'Ez',
        'Daniel':'Da',
        'Hosea':'Ho',
        'Joel':'Jl',
        'Amos':'Am',
        'Obadiah':'Ob',
        'Jonah':'Jnh',
        'Micah':'Mic',
        'Nahum':'Na',
        'Habakkuk':'Hab',
        'Zephaniah':'Zp',
        'Haggai':'Hg',
        'Zachariah':'Zc',
        'Malachi':'Ml',

        # Apocrypha/Deuterocanon
        'Tobiah':'Tb',
        'Judith':'Jdt',
        # 'Additions to Esther' and 'Greek Esther' are included in Esther
        'Wisdom Of Solomon':'Ws','Wisdom':'Ws',
        'Sirach':'Sir',
        'Baruch':'Bar',
        # 'Letter of Jeremiah' has no short form
        'Prayer Of Azariah':'PrAz',
        'Susanna':'Sus',
        'Bel And The Dragon':'Bel',
        '1 Maccabees':'1Ma',
        '2 Maccabees':'2Ma',
        '3 Maccabees':'3Ma',
        '4 Maccabees':'4Ma',
        '1 Esdras':'1Esd',
        '2 Esdras':'2Esd',
        'Prayer Of Manasseh':'PrMan',
        # Psalm 151 is covered by 'Psalm' above.

        # New Testament
        'Matthew':'Mt',
        'Mark':'Mr',
        'Luke':'Lk',
        'John':'Jn',
        'Acts':'Ac',
        'Romans':'Ro',
        '1 Corinthians':'1Co',
        '2 Corinthians':'2Co',
        'Galatians':'Ga',
        'Ephesians':'Ep',
        'Philippians':'Pp',
        'Colossians':'Col',
        '1 Thessalonians':'1Th',
        '2 Thessalonians':'2Th',
        '1 Timothy':'1Tm',
        '2 Timothy':'2Tm',
        'Titus':'Ti',
        'Philemon':'Phm',
        'Hebrews':'He',
        'James':'Jas',
        '1 Peter':'1Pe',
        '2 Peter':'2Pe',
        '1 John':'1Jn',
        '2 John':'2Jn',
        '3 John':'3Jn',
        'Jude':'Jud',
        'Revelation':'Re'
    }

    for book in abbreviations:
        text = text.replace(book, abbreviations[book])

    return text