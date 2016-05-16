import shelve
import argparse
import importlib
from datetime import datetime
from time import mktime
from urllib import request

import feedparser


DATETIME_STORE_FORMAT = '%Y-%m-%d %H:%M:%S'


def update_fetched_history(file_path):
    with shelve.open(file_path) as database:
        fetched_history = database.get('fetched_history', [])
        fetched_history.insert(0, {
            'fetched_at': datetime.now().strftime(DATETIME_STORE_FORMAT)
        })
        database['fetched_history'] = fetched_history


def load_fetched_history(file_path):
    with shelve.open(file_path) as database:
        fetched_history = database.get('fetched_history', [])

    for i, item in enumerate(fetched_history):
        item['fetched_at'] = datetime.strptime(item['fetched_at'], DATETIME_STORE_FORMAT)
        fetched_history[i] = item
    return fetched_history


def fetch_feed(feed_url):
    parsed = feedparser.parse(feed_url)
    feed = parsed.feed
    feed_info = {
      'title': feed.title,
      'subtitle': feed.subtitle,
      'link': feed.link,
      'fetched_at': datetime.now()
    }
    entries = parsed.entries
    return feed_info, entries


def get_entry_body(url):
    body = request.urlopen(url).read().decode('utf-8')
    return body


def get_entry_info(entry):
    return {
        'title': entry.title,
        'link': entry.link,
    }


# Pluginが書けるようにして、FacebookとかHatena Bookmark, Pocketのシェア数を取れるようにする。
# あと、bodyの代わりに形態素解析かけて重要な単語だけを取り出すpluginも欲しい。これで簡単に転置インデックスが作れる。

def convert_struct_time_to_datetime(updated_parsed):
    """Convert struct_time to python datetime object.
    :param time.struct_time updated_parsed: updated_parsed
    :return datetime: datetime
    """
    return datetime.fromtimestamp(mktime(updated_parsed))


class Feedy:
    feeds = {}

    def __init__(self, history_file):
        self.history_file = history_file

    def add(self, feed_url, callback=None):
        def decorator(callback_func):
            self.add_feed(feed_url, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def add_feed(self, feed_url, callback):
        self.feeds[callback.__name__] = (feed_url, callback)

    def _handle(self, callback, entry, feed_info, **kwargs):  # pluginはこの**kwargsでうまいこと制御. pocketの時はpocket_infoを混ぜる
        body = get_entry_body(entry.link)
        callback(feed_info=feed_info, entry_info=entry, body=body, **kwargs)

    def run(self, targets):
        if targets == 'all':
            targets = self.feeds.keys()

        histories = load_fetched_history(self.history_file)
        last_fetched = histories[0]['fetched_at'] if len(histories) == 0 else None

        for target in targets:
            feed_url, callback = self.feeds[target]
            feed_info, entries = fetch_feed(feed_url)

            for entry in entries:
                # 公開日は entry.published_parsed で struct_time が取れる
                # 更新日は entry.updated_parsed でとれる
                if last_fetched and last_fetched < convert_struct_time_to_datetime(entry.updated_parsed):
                    self._handle(callback, entry, feed_info)

        update_fetched_history(self.history_file)


def cmd():
    # これは今のところtargetを自分でargparse書かなくても指定できるコマンドを提供する形になっている
    # TODO: 自分で日付指定もできるようにする。この時はhistoryをどうするか悩みどころ
    # TODO: 最大記事数も指定
    # TODO: データを残さないオプションも欲しい.
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, nargs='?', default='main:feedy',
                        help='Feedy object. ex) main:feedy')
    parser.add_argument('target', type=str, nargs='?', default='all',
                        help='The target function names')
    args = parser.parse_args()

    mod_name, obj = args.filename.split(':')
    mod = importlib.import_module(mod_name)
    runner = getattr(mod, obj)
    runner.run(args.target)
