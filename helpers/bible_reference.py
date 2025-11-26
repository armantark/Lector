"""
Bible reference normalization utilities.

This module consolidates reference-cleaning logic used by different lectionaries
to normalize Bible book abbreviations to their full names.
"""

# USCCB (Catholic) abbreviation mappings - used for UPPERCASE abbreviations
USCCB_ABBREVIATIONS = {
    'GN': 'Genesis',
    'EX': 'Exodus',
    'LV': 'Leviticus',
    'NM': 'Numbers',
    'JDT': 'Judith',  # Must come before DT
    'DT': 'Deuteronomy',
    'JOS': 'Joshua',
    'JGS': 'Judges',
    'RU': 'Ruth',
    '1 SM': '1 Samuel',
    '2 SM': '2 Samuel',
    '1 KGS': '1 Kings',
    '2 KGS': '2 Kings',
    '1 CHR': '1 Chronicles',
    '2 CHR': '2 Chronicles',
    'EZR': 'Ezra',
    'NEH': 'Nehemiah',
    'TB': 'Tobit',
    'EST': 'Esther',
    '1 MC': '1 Maccabees',
    '2 MC': '2 Maccabees',
    'JB': 'Job',
    'PS': 'Psalm',
    'PRV': 'Proverbs',
    'ECCL': 'Ecclesiastes',
    'SGS': 'Song of Songs',
    'WIS': 'Wisdom',
    'SIR': 'Sirach',
    'IS': 'Isaiah',
    'JER': 'Jeremiah',
    'LAM': 'Lamentations',
    'BAR': 'Baruch',
    'EZ': 'Ezekiel',
    'DN': 'Daniel',
    'HOS': 'Hosea',
    'JL': 'Joel',
    'AM': 'Amos',
    'OB': 'Obadiah',
    'JON': 'Jonah',
    'MI': 'Micah',
    'NA': 'Nahum',
    'HB': 'Habakkuk',
    'ZEP': 'Zephaniah',
    'HG': 'Haggai',
    'ZEC': 'Zachariah',
    'MAL': 'Malachi',
    'MT': 'Matthew',
    'MK': 'Mark',
    'LK': 'Luke',
    'JN': 'John',
    'ACTS': 'Acts',
    'ROM': 'Romans',
    '1 COR': '1 Corinthians',
    '2 COR': '2 Corinthians',
    'GAL': 'Galatians',
    'EPH': 'Ephesians',
    'PHIL': 'Philippians',
    'COL': 'Colossians',
    '1 THES': '1 Thessalonians',
    '2 THES': '2 Thessalonians',
    '1 TM': '1 Timothy',
    '2 TM': '2 Timothy',
    'TI': 'Titus',
    'PHLM': 'Philemon',
    'HEB': 'Hebrews',
    'JAS': 'James',
    '1 PT': '1 Peter',
    '2 PT': '2 Peter',
    '1 JN': '1 John',
    '2 JN': '2 John',
    '3 JN': '3 John',
    'JUDE': 'Jude',
    'RV': 'Revelation'
}

# Coptic lectionary abbreviation mappings - used for mixed-case abbreviations
COPTIC_ABBREVIATIONS = {
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


def normalize_usccb_reference(reference: str) -> str:
    """
    Normalize a Bible reference from USCCB format to full book names.
    
    Used by the Catholic lectionary to convert uppercase abbreviations
    like 'GN 1:1' to 'Genesis 1:1'.
    
    Args:
        reference: A Bible reference string with USCCB abbreviations
        
    Returns:
        The reference with the book name expanded to its full form
    """
    reference = reference.upper()
    for abbrev, full_name in USCCB_ABBREVIATIONS.items():
        if f'{abbrev} ' in reference:
            reference = reference.replace(abbrev, full_name)
            break
    return reference.title()


def normalize_coptic_reference(reference: str) -> str:
    """
    Normalize a Bible reference from Coptic Orthodox format.
    
    Used by the Coptic Orthodox lectionary to convert abbreviations
    like 'Matt 5:1' to 'Matthew 5:1' and clean up punctuation.
    
    Args:
        reference: A Bible reference string with Coptic-style abbreviations
        
    Returns:
        The reference with abbreviations expanded
    """
    for abbrev, replacement in COPTIC_ABBREVIATIONS.items():
        reference = reference.replace(abbrev, replacement)
    return reference

