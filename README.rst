=====
Feedy
=====

Decorator-based RSS Feed Fetcher for Python3


Usage
=====

.. code-block:: python

    from feedy import Feedy
    from bs4 import BeautifulSoup

    feedy = Feedy(max_entries=5)

    @feedy.add('http://nwpct1.hatenablog.com/rss')
    def c_bata_web(feed_info, entry_info, body):
        """Get image urls in my blog's article"""
        soup = BeautifulSoup(body, "html.parser")
        for x in soup.find_all('img', {'class': 'hatena-fotolife'}):
            print(x['src'])

    @feedy.add('https://www.djangopackages.com/feeds/packages/latest/rss/')
    def djangopackages(feed_info, entry_info, body):
        """Get the latest django library information."""
        print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))

    if __name__ == '__main__':
        feedy.run('all')


After that, please execute a following command:

::

    $ feedy example:feedy -t djangopackages
    - [django-simple-address](http://www.djangopackages.com/packages/p/django-simple-address/)
    - [django-db-sanitizer](http://www.djangopackages.com/packages/p/django-db-sanitizer/)
    - [fluentcms-jumbotron](http://www.djangopackages.com/packages/p/fluentcms-jumbotron/)
    - [fluentcms-contactform](http://www.djangopackages.com/packages/p/fluentcms-contactform/)
    - [fluentcms-pager](http://www.djangopackages.com/packages/p/fluentcms-pager/)

    $ feedy example:feedy  # Run all when given no target arguments.
    - [django-simple-address](http://www.djangopackages.com/packages/p/django-simple-address/)
    - [django-db-sanitizer](http://www.djangopackages.com/packages/p/django-db-sanitizer/)
    - [fluentcms-jumbotron](http://www.djangopackages.com/packages/p/fluentcms-jumbotron/)
    - [fluentcms-contactform](http://www.djangopackages.com/packages/p/fluentcms-contactform/)
    - [fluentcms-pager](http://www.djangopackages.com/packages/p/fluentcms-pager/)
    - http://cdn-ak.f.st-hatena.com/images/fotolife/n/nwpct1/20160409/20160409180830.png
    - http://cdn-ak.f.st-hatena.com/images/fotolife/n/nwpct1/20160107/20160107173222.png
    - http://cdn-ak.f.st-hatena.com/images/fotolife/n/nwpct1/20160107/20160107173406.jpg


If you want to fetch the updated entries, please specified file_path parameter like ``feedy = Feedy('./feedy.dat')``.


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
