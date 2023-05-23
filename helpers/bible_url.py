import json
import re


def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


REPLACEMENTS = load_json('helpers/replacements.json')
ABBREVIATIONS = load_json('helpers/abbreviations.json')


def convert(reference):
    """
    Converts an individual Bible reference into a neat Markdown link
    """

    # There's a weird nuance with how BibleGateway fetches Psalm 151.
    # Even when you're using a translation that includes it, the term
    # "Psalm 151" throws a "No Results Found" Error unless you write it
    # with a pseudo-chapter number: "Psalm 151 1".
    if reference == "":
        return reference
    if not reference[-1:].isdigit():
        return '*' + reference + '*'

    for item in REPLACEMENTS:
        reference = reference.replace(item, REPLACEMENTS[item])

    anchor = reference

    # Clean up references that have alternative chapter numbers within
    # brackets so the links don't break
    # Ex: '4[2] Kings 2:6-14' => '2 Kings 2:6-14'
    reference = re.sub(r'([0-9]+\[([0-9]+)])', r'\2', reference)

    # Get rid of letter subreferences in verses
    pattern = re.compile(r'([0-9]+)([a-zA-Z]+)')

    # '1 Samuel 2:8ABCD' => '1 Samuel 2:8'
    reference = re.sub(pattern, r'\1', reference)

    # '1 Samuel 2:8ABCD' => '1 Samuel 2:8abcd'
    for item in re.findall(pattern, anchor):
        item = ''.join(item)
        anchor = anchor.replace(item, item.lower())

    reference = shorten(reference).replace(' ', '+')
    return f'[{anchor}](https://biblegateway.com/passage/?search={reference})'


def html_convert(text):
    """
    Converts a string with anchored Bible references to Markdown

    In: "God creates everything\nin <a>Genesis 1:1</a>"
    Out: "God creates everything\nin [Genesis 1:1](https://www.example.com)"
    """
    for match in re.findall(r'(<a>([^<>]*))', text):
        text = text.replace(match[0], convert(match[1]))

    return text


def shorten(text):
    """
    Given a Bible reference, shortens it for linking efficiency
    NOTE: These are optimized for BibleGateway.com
    """

    text = text.replace(', ', ',').replace('; ', ';').title()

    for book in ABBREVIATIONS:
        text = text.replace(book, ABBREVIATIONS[book])

    return text
