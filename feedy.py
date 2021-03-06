import asyncio
import os
import shelve
import sys
from importlib.machinery import SourceFileLoader
from datetime import datetime
from time import mktime
from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG, WARNING, ERROR, Logger
from functools import wraps
from typing import Tuple, Dict, Any

import aiohttp
import click
import feedparser

# Default run parameters #######################################
DEFAULT_RUN_PARAMS: Dict[str, Any] = {
    'targets': None,
    'max_entries': None,
    'ignore_fetched': False,
    'asyncio_semaphore': 5,
}


# Logger settings        #######################################
def _create_logger(name: str) -> Logger:
    formatter = Formatter('[%(levelname)s] %(message)s')
    sh = StreamHandler()
    sh.setFormatter(formatter)
    logger = getLogger(name)
    logger.addHandler(sh)
    return logger

logger: Logger = _create_logger(__name__)


# Shelve store            ########################################
class ShelveStore:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def update_or_create(self, key: str, value: Any) -> None:
        with shelve.open(self.file_path) as db:
            db[key] = value

    def load(self, key: str) -> Any:
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
                'site_title': feed.title,
                'site_subtitle': feed.subtitle,
                'site_url': feed.link,
                'fetched_at': datetime.now()
            }
            entries = parsed.entries
            return feed_info, entries


def _get_entry_info(entry):
    published = datetime.fromtimestamp(mktime(entry.published_parsed)) if hasattr(entry, 'published_parsed') else None
    updated = datetime.fromtimestamp(mktime(entry.updated_parsed)) if hasattr(entry, 'updated_parsed') else None
    return {
        'article_title': entry.title,
        'article_url': entry.link,
        'published_at': published,
        'updated_at': updated,
    }


async def _fetch_body(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def _bound_fetch_body(url, semaphore=DEFAULT_RUN_PARAMS['asyncio_semaphore']):
    sem = asyncio.Semaphore(semaphore)
    async with sem:
        return await _fetch_body(url)


async def _fetch_bodies(entries):
    tasks = [asyncio.ensure_future(_bound_fetch_body(e.link)) for e in entries]
    bodies = asyncio.gather(*tasks)
    return await bodies


def _should_fetch(entry_updated_parsed, ignore_fetched, last_fetched_at):
    if ignore_fetched or last_fetched_at is None:
        return True
    if datetime.fromtimestamp(mktime(entry_updated_parsed)) > last_fetched_at:
        return True
    return False


class Feedy:
    feeds = {}
    plugins = []
    store = None

    def __init__(self, store=None):
        if store:
            self.set_store(store)

    def set_store(self, store):
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
        logger.debug("{} plugin is registered.".format(plugin.__name__))

    def add(self, feed_url, callback=None):
        @wraps(callback)
        def decorator(callback_func):
            self.feeds[callback_func.__name__] = (feed_url, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def entry_handler(self, callback, body, entry, feed_info):
        for plugin in self.plugins:
            callback = plugin(callback) if callable(plugin) else callback

        entry_info = _get_entry_info(entry)
        feed_info.update(entry_info)  # This dict need not copy using `copy.deepcopy()`.
        callback(info=feed_info, body=body)

    def feed_handler(self, callback, loop, feed_info, entries,
                     max_entries=DEFAULT_RUN_PARAMS['max_entries'],
                     ignore_fetched=DEFAULT_RUN_PARAMS['ignore_fetched']):
        last_fetched_at = self.store.load('{}_fetched_at'.format(callback.__name__)) if self.store else None
        entries = [e for e in entries[:max_entries] if _should_fetch(e.updated_parsed, ignore_fetched, last_fetched_at)]
        future = asyncio.ensure_future(_fetch_bodies(entries))
        bodies = loop.run_until_complete(future)

        if not entries:
            logger.info("No updates in {}.".format(callback.__name__))
        if self.store:
            self.store.update_or_create('{}_fetched_at'.format(callback.__name__), datetime.now())
            logger.debug("A last_fetched_at is just updated.")
        else:
            logger.debug("A last_fetched_at isn't updated.")

        for i, entry in enumerate(entries):
            self.entry_handler(callback, bodies[i], entry, feed_info)

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
def insert_import_path_to_sys_modules(import_path):
    """
    When importing a module, Python references the directories in sys.path.
    The default value of sys.path varies depending on the system, But:
    When you start Python with a script, the directory of the script is inserted into sys.path[0].
    So we have to replace sys.path to import object in specified scripts.
    """
    abspath = os.path.abspath(import_path)
    if os.path.isdir(abspath):
        sys.path.insert(0, abspath)
    else:
        sys.path.insert(0, os.path.dirname(abspath))


def set_logger_level(verbose: int):
    logger_level: Tuple[int] = (ERROR, WARNING, INFO, DEBUG)
    logger.setLevel(logger_level[verbose])


@click.command()
@click.argument('filepath', nargs=1, type=click.Path(exists=True))
@click.option('-v', '--verbose', type=click.IntRange(0, 3), count=True, help='Set log level')
@click.option('-t', '--targets', type=str, multiple=True, default=DEFAULT_RUN_PARAMS['targets'],
              help='The target function names.')
@click.option('-m', '--max-entries', type=int, default=DEFAULT_RUN_PARAMS['max_entries'],
              help="The maximum length for fetching entries every RSS feed")
@click.option('--ignore-fetched/--no-ignore-fetched', default=DEFAULT_RUN_PARAMS['ignore_fetched'],
              help="The maximum length for fetching entries every RSS feed")
def cmd(filepath: str, verbose: int, **kwargs) -> None:
    """Run your feedy's project flexibly."""
    set_logger_level(verbose)

    insert_import_path_to_sys_modules(os.path.abspath(filepath))
    module = SourceFileLoader('module', filepath).load_module()
    for objname in dir(module):
        obj = getattr(module, objname)
        if isinstance(obj, Feedy):
            break
    else:
        click.secho("Feedy's instance is not found.", fg='red')
        sys.exit(status=1)
    obj.run(**kwargs)
