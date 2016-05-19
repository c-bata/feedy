import types
import os
import shelve
from datetime import datetime
from time import mktime
from urllib import request

import click
import feedparser


# Store fetched datetime ########################################
class ShelveStore:
    def __init__(self, file_path):
        self.file_path = file_path

    def update_or_create(self, key, value):
        with shelve.open(self.file_path) as db:
            db[key] = value

    def load(self, key):
        with shelve.open(self.file_path) as db:
            return db.get(key, None)


# Fetch feed, entry      ########################################
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
    plugins = []
    store = None

    def __init__(self, store=None, max_entries=None):
        if hasattr(store, 'update_or_create') or hasattr(store, 'load'):
            self.store = store
        elif isinstance(store, str):
            self.store = ShelveStore(store)

        self.max_entries = max_entries

    def install(self, plugin):
        if hasattr(plugin, 'setup'):
            plugin.setup(self)
        self.plugins.append(plugin)

    def add(self, feed_url, callback=None):
        def decorator(callback_func):
            self.add_feed(feed_url, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def add_feed(self, feed_url, callback):
        self.feeds[callback.__name__] = (feed_url, callback)

    def entry_handler(self, callback, entry, feed_info):
        for plugin in self.plugins:
            callback = plugin(callback) if callable(plugin) else callback

        entry_info = _get_entry_info(entry)
        body = _get_entry_body(entry)
        callback(feed_info=feed_info, entry_info=entry_info, body=body)

    def feed_handler(self, callback, feed_info, entries):
        if self.store:
            last_fetched = self.store.load('{feed_name}_fetched_at'.format(feed_name=callback.__name__))
        if self.max_entries:
            entries = entries[:self.max_entries]

        for entry in entries:
            if self.store and last_fetched and last_fetched > datetime.fromtimestamp(mktime(entry.updated_parsed)):
                continue
            self.entry_handler(callback, entry, feed_info)

        if self.store:
            self.store.update_or_create('{feed_name}_fetched_at'.format(feed_name=callback.__name__), datetime.now())

    def run(self, target='all', store_file=None, max_entries=None):
        if target == 'all':
            target = self.feeds.keys()
        if store_file:
            self.store = ShelveStore(store_file)
        if max_entries is not None:
            self.max_entries = max_entries

        for t in target:
            feed_url, callback = self.feeds[t]
            feed_info, entries = _fetch_feed(feed_url)
            self.feed_handler(callback, feed_info, entries)


# Command Line Interface ######################################################
def _get_runner(feedy_obj):
    file_name, obj = feedy_obj.split(':')
    t = types.ModuleType('runner')
    file_path = os.path.abspath(file_name)
    file_path = file_path + '.py' if not file_path.endswith('.py') else file_path
    with open(file_path) as mod:
        exec(compile(mod.read(), file_path, 'exec'), t.__dict__)
    runner = getattr(t, obj)
    return runner


def remove_empty_arguments(callback):
    def wrapper(*args, **kwargs):
        kw = {k: v for k, v in kwargs.items() if v is not None}
        return callback(*args, **kw)
    return wrapper


@click.command()
@click.argument('feedy_obj')
@click.option('--target', '-t', type=str, multiple=True, help='The target function names.')
@click.option('--store_file', '-s', help='A filename for store the fetched data.')
@click.option('--max_entries', help="The maximum length for fetching entries every RSS feed")
@remove_empty_arguments
def cmd(feedy_obj, **kwargs):
    """Run your feedy's project flexibly."""
    runner = _get_runner(feedy_obj)
    runner.run(**kwargs)
