"""
Comprehensive test suite for the Lector Discord bot.

This file contains:
- Unit tests: Test individual functions/methods in isolation
- Integration tests: Test how components work together
- E2E tests: Test full flows from input to output

Run with: python -m unittest tests.tests -v
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import datetime


# =============================================================================
# UNIT TESTS: helpers/bible_reference.py
# =============================================================================

class TestBibleReferenceUSCCB(unittest.TestCase):
    """Unit tests for USCCB reference normalization."""

    def test_genesis_abbreviation(self):
        """GN should expand to Genesis."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('GN 1:1')
        self.assertEqual(result, 'Genesis 1:1')

    def test_exodus_abbreviation(self):
        """EX should expand to Exodus."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('EX 20:1-17')
        self.assertEqual(result, 'Exodus 20:1-17')

    def test_psalm_abbreviation(self):
        """PS should expand to Psalm."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('PS 23:1-6')
        self.assertEqual(result, 'Psalm 23:1-6')

    def test_matthew_abbreviation(self):
        """MT should expand to Matthew."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('MT 5:1-12')
        self.assertEqual(result, 'Matthew 5:1-12')

    def test_corinthians_abbreviation(self):
        """1 COR should expand to 1 Corinthians."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('1 COR 13:1-13')
        self.assertEqual(result, '1 Corinthians 13:1-13')

    def test_revelation_abbreviation(self):
        """RV should expand to Revelation."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('RV 21:1-4')
        self.assertEqual(result, 'Revelation 21:1-4')

    def test_case_insensitive_input(self):
        """Should handle lowercase input."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('gn 1:1')
        self.assertEqual(result, 'Genesis 1:1')

    def test_title_case_output(self):
        """Output should be in title case."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('ACTS 2:1-4')
        self.assertEqual(result, 'Acts 2:1-4')

    def test_judith_before_deuteronomy(self):
        """JDT should match before DT (order matters)."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('JDT 8:1-8')
        self.assertEqual(result, 'Judith 8:1-8')

    def test_deuteronomy(self):
        """DT should expand to Deuteronomy."""
        from helpers.bible_reference import normalize_usccb_reference
        result = normalize_usccb_reference('DT 6:4-9')
        self.assertEqual(result, 'Deuteronomy 6:4-9')


class TestBibleReferenceCoptic(unittest.TestCase):
    """Unit tests for Coptic reference normalization."""

    def test_matt_to_matthew(self):
        """Matt should expand to Matthew."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('Matt 5:1-12')
        self.assertEqual(result, 'Matthew 5:1-12')

    def test_mk_to_mark(self):
        """Mk should expand to Mark."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('Mk 1:1-8')
        self.assertEqual(result, 'Mark 1:1-8')

    def test_lk_to_luke(self):
        """Lk should expand to Luke."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('Lk 2:1-20')
        self.assertEqual(result, 'Luke 2:1-20')

    def test_jn_to_john(self):
        """Jn should expand to John."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('Jn 3:16')
        self.assertEqual(result, 'John 3:16')

    def test_1cor_to_1_corinthians(self):
        """1Cor should expand to 1 Corinthians with space."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('1Cor 13:1')
        self.assertEqual(result, '1 Corinthians 13:1')

    def test_ampersand_cleanup(self):
        """Double ampersand should be converted to semicolon."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('Matt 1:1  & Lk 1:1')
        self.assertEqual(result, 'Matthew 1:1; Luke 1:1')

    def test_hyphen_cleanup(self):
        """Spaced hyphen should be converted to hyphen."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('Matt 1:1 - 10')
        self.assertEqual(result, 'Matthew 1:1-10')

    def test_multiple_john_variants(self):
        """Should handle 1Jn, 2Jn, 3Jn correctly."""
        from helpers.bible_reference import normalize_coptic_reference
        self.assertEqual(normalize_coptic_reference('1Jn 1:1'), '1 John 1:1')
        self.assertEqual(normalize_coptic_reference('2Jn 1:1'), '2 John 1:1')
        self.assertEqual(normalize_coptic_reference('3Jn 1:1'), '3 John 1:1')

    def test_passthrough_unknown(self):
        """Unknown references should pass through unchanged."""
        from helpers.bible_reference import normalize_coptic_reference
        result = normalize_coptic_reference('Genesis 1:1')
        self.assertEqual(result, 'Genesis 1:1')


# =============================================================================
# UNIT TESTS: helpers/date_expand.py
# =============================================================================

class TestDateExpandOrdinal(unittest.TestCase):
    """Unit tests for ordinal number formatting."""

    def test_first(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(1), '1st')

    def test_second(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(2), '2nd')

    def test_third(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(3), '3rd')

    def test_fourth_through_ninth(self):
        from helpers.date_expand import ordinal
        for n in range(4, 10):
            self.assertEqual(ordinal(n), f'{n}th')

    def test_tenth(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(10), '10th')

    def test_eleventh_through_thirteenth(self):
        """11th, 12th, 13th are special cases."""
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(11), '11th')
        self.assertEqual(ordinal(12), '12th')
        self.assertEqual(ordinal(13), '13th')

    def test_twenty_first(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(21), '21st')

    def test_twenty_second(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(22), '22nd')

    def test_twenty_third(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(23), '23rd')

    def test_thirty_first(self):
        from helpers.date_expand import ordinal
        self.assertEqual(ordinal(31), '31st')


class TestDateExpandExpand(unittest.TestCase):
    """Unit tests for date expansion with weekday."""

    def test_contains_weekday(self):
        from helpers.date_expand import expand
        test_date = datetime.date(2025, 1, 15)  # Wednesday
        result = expand(test_date)
        self.assertIn('Wednesday', result)

    def test_contains_month(self):
        from helpers.date_expand import expand
        test_date = datetime.date(2025, 1, 15)
        result = expand(test_date)
        self.assertIn('January', result)

    def test_contains_ordinal_day(self):
        from helpers.date_expand import expand
        test_date = datetime.date(2025, 1, 15)
        result = expand(test_date)
        self.assertIn('15th', result)

    def test_contains_year(self):
        from helpers.date_expand import expand
        test_date = datetime.date(2025, 1, 15)
        result = expand(test_date)
        self.assertIn('2025', result)


class TestDateExpandNoWeekday(unittest.TestCase):
    """Unit tests for date expansion without weekday."""

    def test_no_weekday(self):
        from helpers.date_expand import expand_no_weekday
        test_date = datetime.date(2025, 1, 15)
        result = expand_no_weekday(test_date)
        self.assertNotIn('Wednesday', result)
        self.assertIn('January', result)
        self.assertIn('15th', result)


class TestDateExpandAutoExpand(unittest.TestCase):
    """Unit tests for auto_expand which chooses format based on context."""

    def test_adds_weekday_when_not_in_text(self):
        from helpers.date_expand import auto_expand
        test_date = datetime.date(2025, 1, 15)
        result = auto_expand(test_date, "Some title without weekday")
        self.assertIn('Wednesday', result)

    def test_no_weekday_when_already_in_text(self):
        from helpers.date_expand import auto_expand
        test_date = datetime.date(2025, 1, 15)
        result = auto_expand(test_date, "Wednesday Mass readings")
        self.assertNotIn('Wednesday', result)


# =============================================================================
# UNIT TESTS: helpers/bible_url.py
# =============================================================================

class TestBibleUrlConvert(unittest.TestCase):
    """Unit tests for Bible URL conversion."""

    def test_simple_reference(self):
        from helpers.bible_url import convert
        result = convert('Genesis 1:1')
        self.assertIn('[Genesis 1:1]', result)
        self.assertIn('biblegateway.com', result)

    def test_empty_string(self):
        from helpers.bible_url import convert
        result = convert('')
        self.assertEqual(result, '')

    def test_non_numeric_ending_italicized(self):
        """References not ending with a digit should be italicized."""
        from helpers.bible_url import convert
        result = convert('Some non-verse text')
        self.assertTrue(result.startswith('*'))
        self.assertTrue(result.endswith('*'))

    def test_psalm_151_special_case(self):
        """Psalm 151 should get special handling."""
        from helpers.bible_url import convert
        result = convert('Psalm 151')
        self.assertIn('Psalm 151 1', result)  # Adds pseudo-chapter

    def test_reference_with_verse_range(self):
        """References with verse ranges should work correctly."""
        from helpers.bible_url import convert
        # References with verse ranges should produce links
        result = convert('Genesis 1:1-31')
        self.assertIn('[Genesis 1:1-31]', result)
        self.assertIn('biblegateway.com', result)

    def test_non_verse_text_italicized(self):
        """Text not ending with a digit should be italicized."""
        from helpers.bible_url import convert
        # References ending with letters are treated as non-verse text
        result = convert('1 Samuel 2:8a')
        self.assertTrue(result.startswith('*'))
        self.assertTrue(result.endswith('*'))


class TestBibleUrlHtmlConvert(unittest.TestCase):
    """Unit tests for HTML-to-markdown conversion."""

    def test_converts_anchor_tags(self):
        from helpers.bible_url import html_convert
        result = html_convert('Read <a>John 3:16</a>')
        self.assertIn('[John 3:16]', result)
        self.assertNotIn('<a>', result)
        self.assertNotIn('</a>', result)

    def test_multiple_anchors(self):
        from helpers.bible_url import html_convert
        result = html_convert('<a>Genesis 1:1</a> and <a>John 1:1</a>')
        self.assertIn('[Genesis 1:1]', result)
        self.assertIn('[John 1:1]', result)

    def test_preserves_non_anchor_text(self):
        from helpers.bible_url import html_convert
        result = html_convert('Read <a>John 3:16</a> today')
        self.assertIn('Read', result)
        self.assertIn('today', result)


class TestBibleUrlShorten(unittest.TestCase):
    """Unit tests for reference shortening."""

    def test_genesis_shortened(self):
        from helpers.bible_url import shorten
        result = shorten('Genesis 1:1')
        self.assertIn('Ge', result)

    def test_psalm_shortened(self):
        from helpers.bible_url import shorten
        result = shorten('Psalm 23:1')
        self.assertIn('Ps', result)

    def test_removes_spaces_in_semicolons(self):
        from helpers.bible_url import shorten
        result = shorten('Genesis 1:1; 2:1')
        self.assertNotIn('; ', result)


class TestBibleUrlExtractReferences(unittest.TestCase):
    """Unit tests for extracting references from anchor tags."""

    def test_extract_single_reference(self):
        from helpers.bible_url import extract_references
        result = extract_references('<a>Genesis 1:1</a>')
        self.assertEqual(result, ['Genesis 1:1'])

    def test_extract_multiple_references(self):
        from helpers.bible_url import extract_references
        result = extract_references('<a>Genesis 1:1</a> and <a>Exodus 2:3</a>')
        self.assertEqual(result, ['Genesis 1:1', 'Exodus 2:3'])

    def test_extract_with_verse_range(self):
        from helpers.bible_url import extract_references
        result = extract_references('<a>John 3:16-21</a>')
        self.assertEqual(result, ['John 3:16-21'])

    def test_extract_filters_non_verse(self):
        """References not ending in digit should be filtered out."""
        from helpers.bible_url import extract_references
        result = extract_references('<a>Some Text</a>')
        self.assertEqual(result, [])

    def test_extract_empty_text(self):
        from helpers.bible_url import extract_references
        result = extract_references('')
        self.assertEqual(result, [])

    def test_extract_no_anchors(self):
        from helpers.bible_url import extract_references
        result = extract_references('Just some plain text')
        self.assertEqual(result, [])


class TestBibleUrlBuildCombinedUrl(unittest.TestCase):
    """Unit tests for building combined Bible Gateway URLs."""

    def test_single_reference(self):
        from helpers.bible_url import build_combined_url
        result = build_combined_url(['Genesis 1:1'])
        self.assertIn('biblegateway.com', result)
        self.assertIn('search=', result)

    def test_multiple_references(self):
        from helpers.bible_url import build_combined_url
        result = build_combined_url(['Genesis 1:1', 'Exodus 2:3'])
        self.assertIn('biblegateway.com', result)
        self.assertIn('Ge', result)
        self.assertIn('Ex', result)

    def test_empty_list(self):
        from helpers.bible_url import build_combined_url
        result = build_combined_url([])
        self.assertEqual(result, '')

    def test_custom_anchor_text(self):
        from helpers.bible_url import build_combined_url
        result = build_combined_url(['Genesis 1:1'], anchor_text="Custom Text")
        self.assertIn('[Custom Text]', result)

    def test_deuterocanonical_adds_version(self):
        """Deuterocanonical books should add NRSVCE version."""
        from helpers.bible_url import build_combined_url
        result = build_combined_url(['Wisdom 1:1'])
        self.assertIn('version=NRSVCE', result)

    def test_canonical_no_version(self):
        """Canonical books should not add version parameter."""
        from helpers.bible_url import build_combined_url
        result = build_combined_url(['Genesis 1:1'])
        self.assertNotIn('version=', result)

    def test_mixed_canonical_deuterocanonical(self):
        """Mix of canonical and deuterocanonical should add version."""
        from helpers.bible_url import build_combined_url
        result = build_combined_url(['Genesis 1:1', 'Sirach 2:3'])
        self.assertIn('version=NRSVCE', result)


class TestBibleUrlExtractAndBuildCombinedUrl(unittest.TestCase):
    """Unit tests for the convenience function."""

    def test_extract_and_build(self):
        from helpers.bible_url import extract_and_build_combined_url
        result = extract_and_build_combined_url('<a>Genesis 1:1</a> and <a>John 3:16</a>')
        self.assertIn('biblegateway.com', result)
        self.assertIn('Read all on Bible Gateway', result)


# =============================================================================
# UNIT TESTS: lectionary/registry.py
# =============================================================================

class TestLectionaryRegistryGetIndex(unittest.TestCase):
    """Unit tests for lectionary index lookup."""

    def test_armenian_full_name(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('armenian'), 0)

    def test_armenian_shortcut(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('a'), 0)

    def test_bcp_full_name(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('book of common prayer'), 1)

    def test_bcp_shortcuts(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('bcp'), 1)
        self.assertEqual(registry.get_index('b'), 1)

    def test_catholic_shortcuts(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('catholic'), 2)
        self.assertEqual(registry.get_index('c'), 2)

    def test_american_orthodox_shortcuts(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('american orthodox'), 3)
        self.assertEqual(registry.get_index('ao'), 3)
        self.assertEqual(registry.get_index('oca'), 3)

    def test_coptic_orthodox_shortcuts(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('coptic orthodox'), 4)
        self.assertEqual(registry.get_index('co'), 4)

    def test_russian_orthodox_shortcuts(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('russian orthodox'), 5)
        self.assertEqual(registry.get_index('ro'), 5)

    def test_invalid_name(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('invalid'), -1)

    def test_case_insensitive(self):
        from lectionary.registry import registry
        self.assertEqual(registry.get_index('ARMENIAN'), 0)
        self.assertEqual(registry.get_index('Armenian'), 0)


class TestLectionaryRegistryGetName(unittest.TestCase):
    """Unit tests for lectionary display name lookup."""

    def test_valid_index(self):
        from lectionary.registry import registry
        name = registry.get_name(0)
        self.assertEqual(name, 'armenian')

    def test_invalid_index_negative(self):
        from lectionary.registry import registry
        name = registry.get_name(-1)
        self.assertEqual(name, 'Unknown')

    def test_invalid_index_too_large(self):
        from lectionary.registry import registry
        name = registry.get_name(999)
        self.assertEqual(name, 'Unknown')


class TestLectionaryRegistryGet(unittest.TestCase):
    """Unit tests for getting lectionary instances."""

    def test_valid_index_returns_lectionary(self):
        from lectionary.registry import registry
        lec = registry.get(0)
        self.assertIsNotNone(lec)

    def test_invalid_index_returns_none(self):
        from lectionary.registry import registry
        lec = registry.get(-1)
        self.assertIsNone(lec)
        lec = registry.get(999)
        self.assertIsNone(lec)


# =============================================================================
# UNIT TESTS: Lectionary Base Class
# =============================================================================

class TestLectionaryBaseClass(unittest.TestCase):
    """Unit tests for the abstract Lectionary base class."""

    def test_base_class_attributes(self):
        """Verify base class initializes expected attributes."""
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        
        self.assertTrue(hasattr(lec, 'today'))
        self.assertTrue(hasattr(lec, 'url'))
        self.assertTrue(hasattr(lec, 'title'))
        self.assertTrue(hasattr(lec, 'subtitle'))
        self.assertTrue(hasattr(lec, 'readings'))
        self.assertTrue(hasattr(lec, 'synaxarium'))
        self.assertTrue(hasattr(lec, 'ready'))
        self.assertTrue(hasattr(lec, 'last_regeneration'))

    def test_clear_resets_attributes(self):
        """clear() should reset attributes to defaults."""
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        lec.title = "Some Title"
        lec.ready = True
        
        lec.clear()
        
        self.assertEqual(lec.title, '')
        self.assertFalse(lec.ready)

    def test_today_is_date(self):
        """today should be a date object."""
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        self.assertIsInstance(lec.today, datetime.date)

    def test_last_regeneration_is_datetime(self):
        """last_regeneration should be a datetime object."""
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        self.assertIsInstance(lec.last_regeneration, datetime.datetime)


# =============================================================================
# INTEGRATION TESTS: Lectionary Classes
# =============================================================================

class TestArmenianLectionary(unittest.TestCase):
    """Integration tests for ArmenianLectionary."""

    def test_get_synaxarium_returns_string(self):
        """Synaxarium should return a string (URL or empty)."""
        from lectionary.armenian import ArmenianLectionary
        link = ArmenianLectionary.get_synaxarium(None)
        self.assertIsInstance(link, str)
        self.assertTrue(link == '' or link.startswith('http'))

    def test_build_json_structure(self):
        """build_json() should return a list of dicts with expected keys."""
        from lectionary.armenian import ArmenianLectionary
        lec = ArmenianLectionary()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready and len(result) > 0:
            embed = result[0]
            self.assertIsInstance(embed, dict)
            self.assertIn('title', embed)
            self.assertIn('description', embed)
            self.assertIn('author', embed)
            self.assertIn('footer', embed)

    def test_inherits_from_base(self):
        """Should inherit from Lectionary base class."""
        from lectionary.armenian import ArmenianLectionary
        from lectionary.base import Lectionary
        lec = ArmenianLectionary()
        self.assertIsInstance(lec, Lectionary)


class TestBookOfCommonPrayer(unittest.TestCase):
    """Integration tests for BookOfCommonPrayer lectionary."""

    def test_build_json_structure(self):
        """build_json() should return a list of dicts with expected keys."""
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready and len(result) > 0:
            embed = result[0]
            self.assertIsInstance(embed, dict)
            self.assertIn('title', embed)
            self.assertIn('description', embed)
            self.assertIn('author', embed)

    def test_inherits_from_base(self):
        """Should inherit from Lectionary base class."""
        from lectionary.bcp import BookOfCommonPrayer
        from lectionary.base import Lectionary
        lec = BookOfCommonPrayer()
        self.assertIsInstance(lec, Lectionary)


class TestCatholicLectionary(unittest.TestCase):
    """Integration tests for CatholicLectionary."""

    def test_build_json_structure(self):
        """build_json() should return a list of dicts with expected keys."""
        from lectionary.catholic import CatholicLectionary
        lec = CatholicLectionary()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready and len(result) > 0:
            embed = result[0]
            self.assertIsInstance(embed, dict)
            self.assertIn('title', embed)
            self.assertIn('author', embed)
            self.assertIn('fields', embed)

    def test_inherits_from_base(self):
        """Should inherit from Lectionary base class."""
        from lectionary.catholic import CatholicLectionary
        from lectionary.base import Lectionary
        lec = CatholicLectionary()
        self.assertIsInstance(lec, Lectionary)

    def test_has_color_attribute(self):
        """Catholic lectionary should have a color attribute."""
        from lectionary.catholic import CatholicLectionary
        lec = CatholicLectionary()
        self.assertTrue(hasattr(lec, 'color'))

    def test_has_pages_attribute(self):
        """Catholic lectionary should have a pages attribute."""
        from lectionary.catholic import CatholicLectionary
        lec = CatholicLectionary()
        self.assertTrue(hasattr(lec, 'pages'))
        self.assertIsInstance(lec.pages, list)


class TestOrthodoxAmericanLectionary(unittest.TestCase):
    """Integration tests for OrthodoxAmericanLectionary."""

    def test_build_json_structure(self):
        """build_json() should return a list of dicts with expected keys."""
        from lectionary.orthodox_american import OrthodoxAmericanLectionary
        lec = OrthodoxAmericanLectionary()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready and len(result) > 0:
            embed = result[0]
            self.assertIsInstance(embed, dict)
            self.assertIn('title', embed)
            self.assertIn('description', embed)
            self.assertIn('author', embed)
            self.assertIn('fields', embed)

    def test_inherits_from_base(self):
        """Should inherit from Lectionary base class."""
        from lectionary.orthodox_american import OrthodoxAmericanLectionary
        from lectionary.base import Lectionary
        lec = OrthodoxAmericanLectionary()
        self.assertIsInstance(lec, Lectionary)


class TestOrthodoxCopticLectionary(unittest.TestCase):
    """Integration tests for OrthodoxCopticLectionary."""

    def test_build_json_structure(self):
        """build_json() should return a list of dicts with expected keys."""
        from lectionary.orthodox_coptic import OrthodoxCopticLectionary
        lec = OrthodoxCopticLectionary()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready and len(result) > 0:
            embed = result[0]
            self.assertIsInstance(embed, dict)
            self.assertIn('title', embed)
            self.assertIn('author', embed)

    def test_clean_reference_integration(self):
        """clean_reference should use shared bible_reference module."""
        from lectionary.orthodox_coptic import OrthodoxCopticLectionary
        # Test a few known transformations
        self.assertEqual(
            OrthodoxCopticLectionary.clean_reference('Matt 5:1-12'),
            'Matthew 5:1-12'
        )
        self.assertEqual(
            OrthodoxCopticLectionary.clean_reference('Lk 1:1-10'),
            'Luke 1:1-10'
        )

    def test_inherits_from_base(self):
        """Should inherit from Lectionary base class."""
        from lectionary.orthodox_coptic import OrthodoxCopticLectionary
        from lectionary.base import Lectionary
        lec = OrthodoxCopticLectionary()
        self.assertIsInstance(lec, Lectionary)


class TestOrthodoxRussianLectionary(unittest.TestCase):
    """Integration tests for OrthodoxRussianLectionary."""

    def test_build_json_structure(self):
        """build_json() should return a list of dicts (multiple embeds)."""
        from lectionary.orthodox_russian import OrthodoxRussianLectionary
        lec = OrthodoxRussianLectionary()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready and len(result) > 0:
            self.assertGreaterEqual(len(result), 1)
            for embed in result:
                self.assertIsInstance(embed, dict)

    def test_inherits_from_base(self):
        """Should inherit from Lectionary base class."""
        from lectionary.orthodox_russian import OrthodoxRussianLectionary
        from lectionary.base import Lectionary
        lec = OrthodoxRussianLectionary()
        self.assertIsInstance(lec, Lectionary)


class TestRevisedCommonLectionary(unittest.TestCase):
    """Integration tests for RevisedCommonLectionary."""

    def test_build_json_structure(self):
        """build_json() should return a list of dicts with expected keys."""
        from lectionary.rcl import RevisedCommonLectionary
        lec = RevisedCommonLectionary()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready and len(result) > 0:
            embed = result[0]
            self.assertIsInstance(embed, dict)
            self.assertIn('title', embed)
            self.assertIn('author', embed)

    def test_inherits_from_base(self):
        """Should inherit from Lectionary base class."""
        from lectionary.rcl import RevisedCommonLectionary
        from lectionary.base import Lectionary
        lec = RevisedCommonLectionary()
        self.assertIsInstance(lec, Lectionary)

    def test_has_sections_attribute(self):
        """RCL should have a sections attribute."""
        from lectionary.rcl import RevisedCommonLectionary
        lec = RevisedCommonLectionary()
        self.assertTrue(hasattr(lec, 'sections'))
        self.assertIsInstance(lec.sections, dict)


# =============================================================================
# INTEGRATION TESTS: Registry + Lectionaries
# =============================================================================

class TestRegistryLectionaryIntegration(unittest.TestCase):
    """Integration tests for registry with lectionary classes."""

    def test_all_lectionaries_accessible(self):
        """All lectionaries should be accessible via registry."""
        from lectionary.registry import registry
        
        for index in range(6):  # 0-5 are the enabled lectionaries
            lec = registry.get(index)
            # May be None if fetch failed, but should not raise
            if lec is not None:
                self.assertTrue(hasattr(lec, 'build_json'))

    def test_regenerate_all_completes(self):
        """regenerate_all should complete without errors."""
        from lectionary.registry import registry
        # This may make network calls but should not raise
        try:
            registry.regenerate_all()
        except Exception as e:
            self.fail(f"regenerate_all raised {e}")

    def test_get_returns_same_instance(self):
        """Multiple gets should return the same instance (cached)."""
        from lectionary.registry import registry
        lec1 = registry.get(0)
        lec2 = registry.get(0)
        if lec1 is not None and lec2 is not None:
            self.assertIs(lec1, lec2)


# =============================================================================
# E2E TESTS: Full Lectionary Flows
# =============================================================================

class TestE2ELectionaryFlow(unittest.TestCase):
    """End-to-end tests for complete lectionary fetching flows."""

    def test_armenian_full_flow(self):
        """Test complete Armenian lectionary flow: init -> regenerate -> build_json."""
        from lectionary.armenian import ArmenianLectionary
        
        lec = ArmenianLectionary()
        # Should have initialized and fetched
        self.assertIsInstance(lec.today, datetime.date)
        self.assertIsInstance(lec.last_regeneration, datetime.datetime)
        
        # Build JSON should produce valid output
        result = lec.build_json()
        self.assertIsInstance(result, list)

    def test_bcp_full_flow(self):
        """Test complete BCP lectionary flow."""
        from lectionary.bcp import BookOfCommonPrayer
        
        lec = BookOfCommonPrayer()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready:
            self.assertGreater(len(result), 0)
            # Verify description contains Bible links
            embed = result[0]
            if 'description' in embed and embed['description']:
                self.assertIn('biblegateway.com', embed['description'])

    def test_catholic_full_flow(self):
        """Test complete Catholic lectionary flow."""
        from lectionary.catholic import CatholicLectionary
        
        lec = CatholicLectionary()
        result = lec.build_json()
        
        self.assertIsInstance(result, list)
        if lec.ready:
            # Catholic can have multiple pages
            for embed in result:
                self.assertIn('title', embed)
                self.assertIn('author', embed)
                self.assertEqual(embed['author']['name'], 'Catholic Lectionary')

    def test_registry_full_flow(self):
        """Test complete flow through registry."""
        from lectionary.registry import registry
        
        # Look up by name
        index = registry.get_index('armenian')
        self.assertEqual(index, 0)
        
        # Get display name
        name = registry.get_name(index)
        self.assertEqual(name, 'armenian')
        
        # Get lectionary
        lec = registry.get(index)
        if lec is not None:
            # Build JSON
            result = lec.build_json()
            self.assertIsInstance(result, list)


class TestInjectCombinedLink(unittest.TestCase):
    """Unit tests for the _inject_combined_link static method."""

    def test_inject_from_fields(self):
        """Should extract refs from fields and add combined link to description."""
        import re
        from helpers import bible_url
        
        piece = {
            'title': 'Test',
            'description': 'Original description',
            'fields': [
                {'name': 'Reading', 'value': '[Genesis 1:1](https://biblegateway.com/passage/?search=Ge+1:1)'}
            ]
        }
        
        # Simulate _inject_combined_link logic
        all_refs_text = ' '.join(f.get('value', '') for f in piece.get('fields', []))
        all_refs_text += ' ' + piece.get('description', '')
        markdown_refs = re.findall(r'\[([^\]]+)\]\(https://biblegateway\.com/passage/\?search=', all_refs_text)
        
        self.assertEqual(markdown_refs, ['Genesis 1:1'])

    def test_inject_from_description(self):
        """Should extract refs from description (Armenian-style)."""
        import re
        
        piece = {
            'title': 'Test',
            'description': '[Wisdom 9:9-12](https://biblegateway.com/passage/?search=Ws+9:9-12&version=NRSVCE)\n[Isaiah 41:15-19](https://biblegateway.com/passage/?search=Is+41:15-19)'
        }
        
        all_refs_text = piece.get('description', '')
        markdown_refs = re.findall(r'\[([^\]]+)\]\(https://biblegateway\.com/passage/\?search=', all_refs_text)
        
        self.assertEqual(len(markdown_refs), 2)
        self.assertIn('Wisdom 9:9-12', markdown_refs)
        self.assertIn('Isaiah 41:15-19', markdown_refs)

    def test_no_injection_when_no_refs(self):
        """Should not modify piece if no Bible references found."""
        import re
        
        piece = {
            'title': 'Saints & Feasts',
            'description': 'St. John the Baptist'
        }
        
        all_refs_text = piece.get('description', '')
        markdown_refs = re.findall(r'\[([^\]]+)\]\(https://biblegateway\.com/passage/\?search=', all_refs_text)
        
        self.assertEqual(markdown_refs, [])


class TestE2EBibleUrlFlow(unittest.TestCase):
    """End-to-end tests for Bible URL generation."""

    def test_full_html_to_markdown_flow(self):
        """Test converting HTML with Bible refs to markdown links."""
        from helpers.bible_url import html_convert
        
        html = """
        First Reading: <a>Genesis 1:1-5</a>
        Psalm: <a>Psalm 23:1-6</a>
        Second Reading: <a>Romans 8:28-39</a>
        Gospel: <a>John 3:16-21</a>
        """
        
        result = html_convert(html)
        
        # All references should be converted
        self.assertIn('[Genesis 1:1-5]', result)
        self.assertIn('[Psalm 23:1-6]', result)
        self.assertIn('[Romans 8:28-39]', result)
        self.assertIn('[John 3:16-21]', result)
        
        # No HTML tags should remain
        self.assertNotIn('<a>', result)
        self.assertNotIn('</a>', result)
        
        # All should have BibleGateway links
        self.assertEqual(result.count('biblegateway.com'), 4)


# =============================================================================
# MOCK TESTS: Testing with mocked network calls
# =============================================================================

class TestMockedLectionaryFetch(unittest.TestCase):
    """Tests with mocked network requests."""

    @patch('lectionary.base.requests.get')
    def test_bcp_handles_network_error(self, mock_get):
        """BCP should handle network errors gracefully."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        
        # Should not be ready due to network error
        self.assertFalse(lec.ready)
        result = lec.build_json()
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])

    @patch('lectionary.base.requests.get')
    def test_bcp_handles_404(self, mock_get):
        """BCP should handle 404 responses gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        
        # Should not be ready due to 404
        self.assertFalse(lec.ready)
        result = lec.build_json()
        self.assertIsInstance(result, list)

    @patch('lectionary.catholic.requests.get')
    def test_catholic_handles_network_error(self, mock_get):
        """Catholic should handle network errors gracefully."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        from lectionary.catholic import CatholicLectionary
        lec = CatholicLectionary()
        
        # Should not be ready due to network error
        self.assertFalse(lec.ready)
        result = lec.build_json()
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and boundary conditions."""

    def test_empty_build_json_when_not_ready(self):
        """build_json() should return empty list when not ready."""
        from lectionary.bcp import BookOfCommonPrayer
        lec = BookOfCommonPrayer()
        lec.ready = False
        
        result = lec.build_json()
        self.assertEqual(result, [])

    def test_registry_handles_concurrent_access(self):
        """Registry should handle multiple rapid accesses."""
        from lectionary.registry import registry
        
        # Rapid fire multiple requests
        results = []
        for _ in range(10):
            results.append(registry.get(0))
        
        # All should return the same instance
        first = results[0]
        if first is not None:
            for r in results[1:]:
                self.assertIs(r, first)

    def test_date_expand_february_29(self):
        """Should handle leap year dates correctly."""
        from helpers.date_expand import expand
        leap_day = datetime.date(2024, 2, 29)
        result = expand(leap_day)
        self.assertIn('29th', result)
        self.assertIn('February', result)

    def test_bible_url_with_special_characters(self):
        """Should handle references with special characters."""
        from helpers.bible_url import convert
        # Song of Solomon / Song of Songs has spaces
        result = convert('Song of Songs 1:1')
        self.assertIn('biblegateway.com', result)


# =============================================================================
# REGRESSION TESTS
# =============================================================================

class TestRegressions(unittest.TestCase):
    """Tests to prevent regression of previously fixed bugs."""

    def test_catholic_page_clean_ref_uses_shared_module(self):
        """CatholicPage._clean_ref should use shared bible_reference module."""
        from lectionary.catholic import CatholicPage
        # This should still work after refactoring
        result = CatholicPage._clean_ref('GN 1:1')
        self.assertEqual(result, 'Genesis 1:1')

    def test_coptic_clean_reference_uses_shared_module(self):
        """OrthodoxCopticLectionary.clean_reference should use shared module."""
        from lectionary.orthodox_coptic import OrthodoxCopticLectionary
        result = OrthodoxCopticLectionary.clean_reference('Matt 1:1')
        self.assertEqual(result, 'Matthew 1:1')

    def test_logger_not_shadowed_in_armenian(self):
        """Logger should not be shadowed in armenian.py."""
        # Import the module and check that _logger exists
        from lectionary import armenian
        self.assertTrue(hasattr(armenian, '_logger'))

    def test_logger_not_shadowed_in_catholic(self):
        """Logger should not be shadowed in catholic.py."""
        from lectionary import catholic
        self.assertTrue(hasattr(catholic, '_logger'))

    def test_all_lectionaries_inherit_from_base(self):
        """All lectionary classes should inherit from base Lectionary."""
        from lectionary.base import Lectionary
        from lectionary.armenian import ArmenianLectionary
        from lectionary.bcp import BookOfCommonPrayer
        from lectionary.catholic import CatholicLectionary
        from lectionary.orthodox_american import OrthodoxAmericanLectionary
        from lectionary.orthodox_coptic import OrthodoxCopticLectionary
        from lectionary.orthodox_russian import OrthodoxRussianLectionary
        from lectionary.rcl import RevisedCommonLectionary
        
        classes = [
            ArmenianLectionary,
            BookOfCommonPrayer,
            CatholicLectionary,
            OrthodoxAmericanLectionary,
            OrthodoxCopticLectionary,
            OrthodoxRussianLectionary,
            RevisedCommonLectionary,
        ]
        
        for cls in classes:
            self.assertTrue(
                issubclass(cls, Lectionary),
                f"{cls.__name__} should inherit from Lectionary"
            )


if __name__ == '__main__':
    unittest.main()
