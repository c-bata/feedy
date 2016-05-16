from unittest import TestCase
from unittest.mock import MagicMock
from datetime import datetime

import feedparser
from feedy import _get_entry_info


class EntryTests(TestCase):
    def setUp(self):
        self.entry = MagicMock(spec=feedparser.FeedParserDict)
        self.entry.title = 'Title'
        self.entry.link = 'Link'
        self.entry.published_parsed = datetime(2016, 1, 1).timetuple()
        self.entry.updated_parsed = datetime(2016, 1, 2).timetuple()

    def test_get_entry_info(self):
        actual = _get_entry_info(self.entry)
        self.assertEqual(actual['title'], 'Title')
        self.assertEqual(actual['link'], 'Link')
        self.assertEqual(actual['published_at'], datetime(2016, 1, 1))
        self.assertEqual(actual['updated_at'], datetime(2016, 1, 2))

    def test_get_entry_info_when_datetime_does_not_exist(self):
        del self.entry.published_parsed
        del self.entry.updated_parsed

        actual = _get_entry_info(self.entry)
        self.assertIsNone(actual['published_at'])
        self.assertIsNone(actual['updated_at'])
