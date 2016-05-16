=====
Feedy
=====

Decorator-based RSS Feed Fetcher for Python3


Usage
=====

.. code-block:: python

    from feedy import Feedy
    from bs4 import BeautifulSoup

    feedy = Feedy('./history.dat')

    @feedy.add('http://rss/feed/url’)
    def site_a(fetch_info, body):
        """
        :param fetch_info: It has some information(url, title, description, fetched_at)
        :param response: The result of requests.get('article url')
        """
        soup = BeautifulSoup(body)  # You can select your favorite html parser.
        #
        # Storing in DB

And execute following command from the job of crontab:

::

    $ feedy filename:feedy site_name


Command Line Interface
======================

::

    feedy


Requirements
============

* feedparser


Resources
=========

* `Github <https://github.com/c-bata/feedy>`_
* `PyPI <https://pypi.python.org/pypi/feedy>`_
