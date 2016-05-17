import argparse
import importlib
import shelve
from datetime import datetime
from time import mktime
from urllib import request

import feedparser


class ShelveStore:
    def __init__(self, file_path):
        self.file_path = file_path

    def update_or_create(self, key, value):
        with shelve.open(self.file_path) as db:
            db[key] = value

    def load(self, key):
        with shelve.open(self.file_path) as db:
            return db.get(key, None)


def _fetch_feed(feed_url):
    parsed = feedparser.parse(feed_url)
    feed = parsed.feed
    feed_info = {
        'title': feed.title,
        'subtitle': feed.subtitle,
        'site_url': feed.link,
        'fetched_at': datetime.now()
    }
    entries = parsed.entries
    return feed_info, entries


def _get_entry_info(entry):
    published = datetime.fromtimestamp(mktime(entry.published_parsed)) if hasattr(entry, 'published_parsed') else None
    updated = datetime.fromtimestamp(mktime(entry.updated_parsed)) if hasattr(entry, 'updated_parsed') else None
    return {
        'title': entry.title,
        'link': entry.link,
        'published_at': published,
        'updated_at': updated,
    }


def _get_entry_body(entry):
    with request.urlopen(entry.link) as response:
        body = response.read().decode('utf-8')
    return body


class Feedy:
    feeds = {}
    store = None

    def __init__(self, history_file=None, max_entries=None, store=None):
        if history_file and store:
            pass
        elif store:
            self.store = store
        elif history_file:
            self.store = ShelveStore(history_file)
        else:
            self.store = None

        self.max_entries = max_entries

    def add(self, feed_url, callback=None):
        def decorator(callback_func):
            self.add_feed(feed_url, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def add_feed(self, feed_url, callback):
        self.feeds[callback.__name__] = (feed_url, callback)

    def _handle(self, callback, entry, feed_info, **kw):
        entry_info = _get_entry_info(entry)
        body = _get_entry_body(entry)
        callback(feed_info=feed_info, entry_info=entry_info, body=body, **kw)

    def run(self, targets):
        if targets == 'all':
            targets = self.feeds.keys()

        for target in targets:
            feed_url, callback = self.feeds[target]
            feed_info, entries = _fetch_feed(feed_url)

            if self.store:
                last_fetched = self.store.load('{feed_name}_fetched_at'.format(feed_name=callback.__name__))
            if self.max_entries:
                entries = entries[:self.max_entries]

            for entry in entries:
                if self.store and last_fetched and last_fetched > datetime.fromtimestamp(mktime(entry.updated_parsed)):
                    continue
                self._handle(callback, entry, feed_info)

            if self.store:
                self.store.update_or_create('{feed_name}_fetched_at'.format(feed_name=callback.__name__),
                                            datetime.now())


def cmd():
    parser = argparse.ArgumentParser("Run your feedy's project flexibly.")
    parser.add_argument('obj', type=str, nargs=None, help="Feedy's object like: <filename>:<obj>")
    parser.add_argument('-t', '--target', type=str, nargs='+', default='all', help='The target function names')
    args = parser.parse_args()

    mod_name, obj = args.obj.split(':')
    mod = importlib.import_module(mod_name)
    runner = getattr(mod, obj)
    runner.run(args.target)
