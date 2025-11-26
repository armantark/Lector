import json
import re


def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


REPLACEMENTS = load_json('helpers/replacements.json')
ABBREVIATIONS = load_json('helpers/abbreviations.json')
DEUTEROCANON = load_json('helpers/deuterocanon.json')


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
    reference_code = reference.split("+")[0]
    is_apocrypha = reference_code in DEUTEROCANON
    url = f'[{anchor}](https://biblegateway.com/passage/?search={reference}'
    if is_apocrypha:
        url += "&version=NRSVCE"  # can change later
    url += ")"
    return url

def html_convert(text):
    """
    Converts a string with anchored Bible references to Markdown

    In: "God creates everything\nin <a>Genesis 1:1</a>"
    Out: "God creates everything\nin [Genesis 1:1](https://www.example.com)"
    """
    for match in re.findall(r'(<\s*a\s*>([^<>]*)<\s*/\s*a\s*>)', text):
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


def extract_references(text):
    """
    Extract raw Bible references from <a> tags in text.
    
    In: "<a>Genesis 1:1</a> and <a>Exodus 2:3</a>"
    Out: ["Genesis 1:1", "Exodus 2:3"]
    """
    matches = re.findall(r'<\s*a\s*>([^<>]*)<\s*/\s*a\s*>', text)
    # Filter out empty references and non-verse references (those not ending in a digit)
    return [ref for ref in matches if ref and ref[-1:].isdigit()]


def _clean_reference_for_url(reference):
    """
    Clean a single reference for use in a combined URL.
    Similar to convert() but returns just the cleaned reference string.
    """
    for item in REPLACEMENTS:
        reference = reference.replace(item, REPLACEMENTS[item])
    
    # Clean up alternative chapter numbers: '4[2] Kings 2:6-14' => '2 Kings 2:6-14'
    reference = re.sub(r'([0-9]+\[([0-9]+)])', r'\2', reference)
    
    # Remove letter subreferences: '1 Samuel 2:8ABCD' => '1 Samuel 2:8'
    reference = re.sub(r'([0-9]+)([a-zA-Z]+)', r'\1', reference)
    
    return reference


def _check_has_deuterocanon(references):
    """
    Check if any reference in the list is from a deuterocanonical book.
    """
    for reference in references:
        shortened = shorten(reference)
        reference_code = shortened.split(" ")[0].split("+")[0]
        if reference_code in DEUTEROCANON:
            return True
    return False


def build_combined_url(references, anchor_text="Read all on Bible Gateway"):
    """
    Build a single Bible Gateway URL for multiple references.
    
    Args:
        references: List of Bible reference strings (e.g., ["Genesis 1:1", "Exodus 2:3"])
        anchor_text: The display text for the markdown link
        
    Returns:
        A markdown link string, or empty string if no valid references
    """
    if not references:
        return ""
    
    # Clean and shorten each reference for URL
    cleaned_refs = []
    for ref in references:
        cleaned = _clean_reference_for_url(ref)
        shortened = shorten(cleaned)
        cleaned_refs.append(shortened)
    
    # Join references with comma (URL encoded as %2C but BibleGateway accepts comma)
    search_param = ", ".join(cleaned_refs).replace(' ', '+')
    
    # Build the URL
    url = f"https://www.biblegateway.com/passage/?search={search_param}"
    
    # Add version parameter if any deuterocanonical books are present
    if _check_has_deuterocanon(references):
        url += "&version=NRSVCE"
    
    return f"[{anchor_text}]({url})"


def extract_and_build_combined_url(text, anchor_text="Read all on Bible Gateway"):
    """
    Convenience function: extract references from text and build a combined URL.
    
    Args:
        text: Text containing <a> tagged Bible references
        anchor_text: The display text for the markdown link
        
    Returns:
        A markdown link string, or empty string if no valid references found
    """
    references = extract_references(text)
    return build_combined_url(references, anchor_text)
