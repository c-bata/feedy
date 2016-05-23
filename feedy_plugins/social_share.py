"""
A plugin for getting social share counts.

* `Facebook <https://www.facebook.com/>`_
* `Pocket <http://getpocket.com/>`_
* `HatenaBookMark <http://b.hatena.ne.jp/>`_
"""

import asyncio
from urllib import parse
from functools import wraps

import aiohttp
from bs4 import BeautifulSoup
from feedy import logger


async def _get_facebook_info(url):
    base_url = 'http://api.facebook.com/method/fql.query?'
    params = [
        ('query', "select total_count,like_count from link_stat where url='{url}'".format(url=url)),
    ]
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + parse.urlencode(params)) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            return {
                'facebook_likes': int(soup.find('like_count').text),
                'facebook_count': int(soup.find('total_count').text),
            }


async def _get_pocket_info(url):
    base_url = 'http://widgets.getpocket.com/v1/button?'
    params = [
        ('v', '1'),
        ('count', 'horizontal'),
        ('url', url),
    ]
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + parse.urlencode(params)) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            count = int(soup.find('em', {'id': 'cnt'}).text)
            return {
                'pocket_count': count
            }


async def _get_hatena_info(url):
    base_url = 'http://b.hatena.ne.jp/entry/json/?'
    params = [
        ('url', url),
    ]
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + parse.urlencode(params)) as response:
            res = await response.json()
            return {
                'hatebu_count': res.get('count') if res else None,
                'hatebu_related': res.get('related') if res else None,
                'hatebu_bookmarks': res.get('bookmarks') if res else None,
                'hatebu_screenshot': res.get('screenshot') if res else None,
            }


async def _get_social_info(url):
    tasks = [
        asyncio.ensure_future(_get_facebook_info(url)),
        asyncio.ensure_future(_get_pocket_info(url)),
        asyncio.ensure_future(_get_hatena_info(url)),
    ]
    results = await asyncio.gather(*tasks)
    return results


def social_share_plugin(callback):
    @wraps(callback)
    def wrapper(*args, **kwargs):
        url = kwargs['entry_info']['link']
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(_get_social_info(url))
        logger.debug(results)

        social_count = {}
        for result in results:
            social_count.update(result)
        kwargs['social_count'] = social_count
        callback(*args, **kwargs)
    return wrapper
