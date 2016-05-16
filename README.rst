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
    def site_a(feed_info, entry_info, body):
        soup = BeautifulSoup(body)  # You can select your favorite html parser.

        # Storing in DB or Output to console like:
        print(feed_info['title'], ':', entry_info['title'])

        # Get image urls:
        for x in soup.find_all('img'):
            print(x['src'])

And execute following command from the job of crontab:

::

    $ feedy filename:feedy -t site_a


Command Line Interface
======================

::

    $ feedy -h
    usage: Run your feedy's project flexibly. [-h] [-t TARGET [TARGET ...]] obj

    positional arguments:
      obj                   Specify feedy object (style. <filename:obj>)

    optional arguments:
      -h, --help            show this help message and exit
      -t TARGET [TARGET ...], --target TARGET [TARGET ...]
                            The target function names



Requirements
============

* feedparser


Resources
=========

* `Github <https://github.com/c-bata/feedy>`_
* `PyPI <https://pypi.python.org/pypi/feedy>`_
