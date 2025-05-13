import unittest
from lectionary.armenian import ArmenianLectionary
from unittest.mock import patch
import datetime


# TODO: write tests
class MyTestCase(unittest.TestCase):

    def test_get_synaxarium(self):
        link = ArmenianLectionary.get_synaxarium(None)
        print("Today's synaxarium link:", link)
        self.assertIsInstance(link, str)
        # Optionally, check for a valid URL or empty string
        self.assertTrue(link == '' or link.startswith('http'))

    def test_get_synaxarium_may_11_2025(self):
        test_date = datetime.date(2025, 5, 11)
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = test_date
            mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)
            link = ArmenianLectionary.get_synaxarium(None)
            print("Synaxarium link for May 11, 2025:", link)
            self.assertIsInstance(link, str)
            self.assertTrue(link == '' or link.startswith('http'))


if __name__ == '__main__':
    unittest.main()
