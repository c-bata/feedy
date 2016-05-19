import types
import shelve
from datetime import datetime
from time import mktime
from urllib import request
from logging import getLogger, INFO, DEBUG, WARNING, ERROR
from functools import wraps

import click
import feedparser

logger = getLogger(__name__)


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

    def __init__(self, store=None, max_entries=None, ignore_fetched=False):
        if store:
            self.set_store(store)
        self.max_entries = max_entries
        self.ignore_fetched = ignore_fetched

    def install(self, plugin):
        if hasattr(plugin, 'setup'):
            plugin.setup(self)
        self.plugins.append(plugin)

    def add(self, feed_url, callback=None):
        @wraps(callback)
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
        if not self.ignore_fetched:
            if self.store:
                last_fetched = self.store.load('{feed_name}_fetched_at'.format(feed_name=callback.__name__))
            else:
                logger.error("A ignore_fetched is True, but store is not set.")
        if self.max_entries:
            entries = entries[:self.max_entries]

        for entry in entries:
            if self.store and last_fetched and last_fetched > datetime.fromtimestamp(mktime(entry.updated_parsed)):
                continue
            self.entry_handler(callback, entry, feed_info)

        if not self.ignore_fetched:
            if self.store:
                self.store.update_or_create('{feed_name}_fetched_at'.format(feed_name=callback.__name__),
                                            datetime.now())
            else:
                logger.error("A ignore_fetched is True, but store is not set.")

    def set_store(self, store):
        """ Set store """
        if hasattr(store, 'update_or_create') or hasattr(store, 'load'):
            self.store = store
        elif isinstance(store, str):
            self.store = ShelveStore(store)
        else:
            raise TypeError("Store must be string or implement ``.update_or_create()`` and ``load()``.")

    def run(self, targets=None, store=None, max_entries=None, ignore_fetched=None):
        if targets is None:
            targets = self.feeds.keys()
        if store:
            self.store = ShelveStore(store)
        if max_entries is not None:
            self.max_entries = max_entries
        if ignore_fetched != self.ignore_fetched:
            self.ignore_fetched = ignore_fetched

        for t in targets:
            feed_url, callback = self.feeds[t]
            feed_info, entries = _fetch_feed(feed_url)
            self.feed_handler(callback, feed_info, entries)


# Command Line Interface ######################################################
def _get_runner(src, obj):
    t = types.ModuleType('runner')
    with src as mod:
        exec(compile(mod.read(), src.name, 'exec'), t.__dict__)
    runner = getattr(t, obj)
    return runner


def set_logger_level(verbose):
    logger_level = (ERROR, WARNING, INFO, DEBUG)
    logger.setLevel(logger_level[verbose])


def wrangle_arg(kwargs):
    kw = {}
    for k, v in kwargs.items():
        if k == 'targets' and v != ():
            kw[k] = v
        if k == 'store' and v is not None:
            kw[k] = v
        if k == 'max-entries' and v is not None:
            kw[k] = v
        if k == 'ignore-fetched' and v is not None:
            kw[k] = v
    return kw


@click.command()
@click.argument('src', type=click.File('r'), nargs=1)
@click.argument('obj', nargs=1)
@click.option('-v', '--verbose', type=click.IntRange(0, 3), count=True, help='Set log level')
@click.option('-t', '--targets', type=str, multiple=True, help='The target function names.')
@click.option('-s', '--store', type=str, help='A filename for store the last fetched time each RSS feed.')
@click.option('-m', '--max-entries', type=int, help="The maximum length for fetching entries every RSS feed")
@click.option('--ignore-fetched/--no-ignore-fetched', help="The maximum length for fetching entries every RSS feed")
def cmd(src, obj, verbose, **kwargs):
    """Run your feedy's project flexibly."""
    set_logger_level(verbose)
    runner = _get_runner(src, obj)
    kw = wrangle_arg(kwargs)
    runner.run(**kw)
