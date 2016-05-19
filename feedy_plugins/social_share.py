"""
A plugin for getting social share counts.

* `Facebook <https://www.facebook.com/>`_
* `Pocket <http://getpocket.com/>`_
* `HatenaBookMark <http://b.hatena.ne.jp/>`_
"""

import json
from urllib import parse, request
from functools import wraps

from bs4 import BeautifulSoup


def _get_facebook_share_count(url):
    base_url = 'http://api.facebook.com/method/fql.query?'
    params = [
        ('query', "select total_count,like_count from link_stat where url='{url}'".format(url=url)),
    ]
    with request.urlopen(base_url + parse.urlencode(params)) as response:
        html = response.read().decode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    return {
        'facebook_likes': int(soup.find('like_count').text),
        'facebook_count': int(soup.find('total_count').text),
    }


def _get_pocket_saved_count(url):
    base_url = 'http://widgets.getpocket.com/v1/button?'
    params = [
        ('v', '1'),
        ('count', 'horizontal'),
        ('url', url),
    ]
    with request.urlopen(base_url + parse.urlencode(params)) as response:
        html = response.read().decode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    count = int(soup.find('em', {'id': 'cnt'}).text)
    return {
        'pocket_count': count
    }


def _get_hatebu_count(url):
    base_url = 'http://b.hatena.ne.jp/entry/json/?'
    params = [
        ('url', url),
    ]
    with request.urlopen(base_url + parse.urlencode(params)) as response:
        res = json.loads(response.read().decode('utf-8'))
    if res is None:
        # Sometimes, it cannot get response.
        return {'hatebu_count': None, 'hatebu_related': None, 'hatebu_bookmarks': None, 'hatebu_screenshot': None}
    return {
        'hatebu_count': res.get('count'),
        'hatebu_related': res.get('related'),
        'hatebu_bookmarks': res.get('bookmarks'),
        'hatebu_screenshot': res.get('screenshot'),
    }


def social_share_plugin(callback):
    @wraps(callback)
    def wrapper(*args, **kwargs):
        social_count = {}
        url = kwargs['entry_info']['link']
        social_count.update(_get_facebook_share_count(url))
        social_count.update(_get_pocket_saved_count(url))
        social_count.update(_get_hatebu_count(url))
        kwargs['social_count'] = social_count
        callback(*args, **kwargs)
    return wrapper
