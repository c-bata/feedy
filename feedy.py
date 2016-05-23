import asyncio
import types
import shelve
from datetime import datetime
from time import mktime
from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG, WARNING, ERROR
from functools import wraps

import aiohttp
import click
import feedparser

# Default run parameters #######################################
DEFAULT_RUN_PARAMS = {
    'targets': None,
    'max_entries': None,
    'ignore_fetched': False,
}


# Logger settings        #######################################
def _create_logger(name):
    formatter = Formatter('[%(levelname)s] %(message)s')
    sh = StreamHandler()
    sh.setFormatter(formatter)
    logger = getLogger(name)
    logger.addHandler(sh)
    return logger

logger = _create_logger(__name__)


# Shelve store            ########################################
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
async def _fetch_feed(feed_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(feed_url) as response:
            body = await response.text()
            parsed = feedparser.parse(body)
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


async def _get_entry_body(entry):
    async with aiohttp.ClientSession() as session:
        async with session.get(entry.link) as response:
            body = await response.text()
            return body


async def _get_entry_bodies(entries):
    tasks = [asyncio.ensure_future(_get_entry_body(e)) for e in entries]
    bodies = asyncio.gather(*tasks)
    return await bodies


class Feedy:
    feeds = {}
    plugins = []
    store = None

    def __init__(self, store=None):
        if store:
            self.set_store(store)

    def set_store(self, store):
        """ Set store """
        if hasattr(store, 'update_or_create') or hasattr(store, 'load'):
            self.store = store
        elif isinstance(store, str):
            self.store = ShelveStore(store)
        else:
            raise TypeError("Store must be string or implement ``.update_or_create()`` and ``load()``.")

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

    def entry_handler(self, callback, body, entry, feed_info):
        for plugin in self.plugins:
            callback = plugin(callback) if callable(plugin) else callback

        entry_info = _get_entry_info(entry)
        callback(feed_info=feed_info, entry_info=entry_info, body=body)

    def feed_handler(self, callback, loop, feed_info, entries,
                     max_entries=DEFAULT_RUN_PARAMS['max_entries'],
                     ignore_fetched=DEFAULT_RUN_PARAMS['ignore_fetched']):
        if ignore_fetched:
            if self.store:
                last_fetched = self.store.load('{feed_name}_fetched_at'.format(feed_name=callback.__name__))
            else:
                logger.error("A ignore_fetched is True, but store is not set.")
        if max_entries:
            entries = entries[:max_entries]

        future = asyncio.ensure_future(_get_entry_bodies(entries))
        bodies = loop.run_until_complete(future)

        for i, entry in enumerate(entries):
            if self.store and last_fetched and last_fetched > datetime.fromtimestamp(mktime(entry.updated_parsed)):
                continue
            self.entry_handler(callback, bodies[i], entry, feed_info)

        if ignore_fetched:
            if self.store:
                self.store.update_or_create('{feed_name}_fetched_at'.format(feed_name=callback.__name__),
                                            datetime.now())
            else:
                logger.error("A ignore_fetched is True, but store is not set.")

    def target_handler(self, target, loop,
                       max_entries=DEFAULT_RUN_PARAMS['max_entries'],
                       ignore_fetched=DEFAULT_RUN_PARAMS['ignore_fetched']):
        feed_url, callback = self.feeds[target]
        fetched_feed = loop.run_until_complete(_fetch_feed(feed_url))
        feed_info, entries = fetched_feed
        self.feed_handler(callback, loop, feed_info, entries, max_entries=max_entries, ignore_fetched=ignore_fetched)

    def run(self, targets=DEFAULT_RUN_PARAMS['targets'], **kwargs):
        if not targets:
            targets = self.feeds.keys()

        loop = asyncio.get_event_loop()
        for t in targets:
            self.target_handler(t, loop, **kwargs)
        loop.close()


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


@click.command()
@click.argument('src', type=click.File('r'), nargs=1)
@click.argument('obj', nargs=1)
@click.option('-v', '--verbose', type=click.IntRange(0, 3), count=True, help='Set log level')
@click.option('-t', '--targets', type=str, multiple=True, default=DEFAULT_RUN_PARAMS['targets'],
              help='The target function names.')
@click.option('-m', '--max-entries', type=int, default=DEFAULT_RUN_PARAMS['max_entries'],
              help="The maximum length for fetching entries every RSS feed")
@click.option('--ignore-fetched/--no-ignore-fetched', default=DEFAULT_RUN_PARAMS['ignore_fetched'],
              help="The maximum length for fetching entries every RSS feed")
def cmd(src, obj, verbose, **kwargs):
    """Run your feedy's project flexibly."""
    set_logger_level(verbose)
    runner = _get_runner(src, obj)
    runner.run(**kwargs)
