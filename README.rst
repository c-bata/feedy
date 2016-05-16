=====
Feedy
=====

Decorator-based RSS Feed Fetcher for Python3


Usage
=====

.. code-block:: python

    from feedy import Feedy
    from bs4 import BeautifulSoup

    feed = Feedy()

    @feed.add('http://rss/feed/url’)
    def feed_name(fetch_info, response):
        """
        :param fetch_info: It has some information(url, title, description, fetched_at)
        :param response: The result of requests.get('article url')
        """
        soup = BeautifulSoup(response.body)  # You can select your favorite html parser.
        #
        # Storing in DB

And execute following command from the job of crontab:

::

    $ feedy feed_name -o result.json

Requirements
============

* beautifulsoup4
* requets


Resources
=========

* `Github <https://github.com/c-bata/feedy>`_
* `PyPI <https://pypi.python.org/pypi/feedy>`_
