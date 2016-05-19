=====
Feedy
=====

Simple RSS Feed Fetching Framework.


=========
Tutorials
=========

0. Installation
---------------

Supported python version is Python3.

::

    pip install feedy


1. Getting feed entry's title and link
--------------------------------------

Creating ``main.py`` like:

.. code-block:: python

    from feedy import Feedy

    app = Feedy()

    @app.add('https://www.djangopackages.com/feeds/packages/latest/rss/')
    def djangopackages(feed_info, entry_info, body):
        """Get the latest django library information."""
        print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))

    if __name__ == '__main__':
        app.run()


And running:

::

    $ python main.py
    - [django-dynamic-views](http://www.djangopackages.com/packages/p/django-dynamic-views/)
    - [django-simple-address](http://www.djangopackages.com/packages/p/django-simple-address/)
    - [django-db-sanitizer](http://www.djangopackages.com/packages/p/django-db-sanitizer/)
    :


2. Getting only newest feed entries
-----------------------------------

.. code-block:: python

    from feedy import Feedy

    app = Feedy(store='feedy.dat', ignore_fetched=True)

    @app.add('https://www.djangopackages.com/feeds/packages/latest/rss/')
    def djangopackages(feed_info, entry_info, body):
        """Get the latest django library information."""
        print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))

    if __name__ == '__main__':
        app.run()


And running:

::

    $ python main.py
    - [django-dynamic-views](http://www.djangopackages.com/packages/p/django-dynamic-views/)
    - [django-simple-address](http://www.djangopackages.com/packages/p/django-simple-address/)
    - [django-db-sanitizer](http://www.djangopackages.com/packages/p/django-db-sanitizer/)
    :
    :
    $ python main.py  # This is no output because There are no newest feed.
    $

It displays only newest feed entries.


3. Add feed patterns
--------------------

Add CNN news feed for collecting images on each articles.

.. code-block:: python

    from feedy import Feedy
    from bs4 import BeautifulSoup  # You can select your favorite html parser.

    app = Feedy(store='feedy.dat', ignore_fetched=True)

    @app.add('http://rss.cnn.com/rss/edition.rss')
    def cnn(feed_info, entry_info, body):
        soup = BeautifulSoup(body, "html.parser")
        for x in soup.find_all('img'):
            print(x['src'])

    @app.add('https://www.djangopackages.com/feeds/packages/latest/rss/')
    def djangopackages(feed_info, entry_info, body):
        """Get the latest django library information."""
        print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))

    if __name__ == '__main__':
        app.run()

And running:

::

    $ python main.py
    - [django-dynamic-views](http://www.djangopackages.com/packages/p/django-dynamic-views/)
    - [django-simple-address](http://www.djangopackages.com/packages/p/django-simple-address/)
    - [django-db-sanitizer](http://www.djangopackages.com/packages/p/django-db-sanitizer/)
    :
    :
    http://i.cdn.turner.com/cnn/.e1mo/img/4.0/logos/menu_money.png
    http://i.cdn.turner.com/cnn/.e1mo/img/4.0/logos/menu_style.png
    http://edition.i.cdn.cnn.com/.a/1.269.4/assets/logo_cnn_nav_bottom.png
    :
    :


4. Command line interface
-------------------------

Feedy offers command line interface. It's useful for debugging

**help messages**

::

    $ feedy --help
    Usage: feedy [OPTIONS] SRC OBJ

      Run your feedy's project flexibly.

    Options:
      -v, --verbose                   Set log level
      -t, --targets TEXT              The target function names.
      -s, --store TEXT                A filename for store the last fetched time
                                      each RSS feed.
      -m, --max-entries INTEGER       The maximum length for fetching entries
                                      every RSS feed
      --ignore-fetched / --no-ignore-fetched
                                      The maximum length for fetching entries
                                      every RSS feed
      --help                          Show this message and exit.


If you want to get specified entry for debugging, please execute following command:

::

    $ feedy main.py app --max-entries 2 --no-ignore-fetched
    - [django-dynamic-views](http://www.djangopackages.com/packages/p/django-dynamic-views/)
    - [django-simple-address](http://www.djangopackages.com/packages/p/django-simple-address/)
    http://i.cdn.turner.com/cnn/.e1mo/img/4.0/logos/menu_money.png
    http://i.cdn.turner.com/cnn/.e1mo/img/4.0/logos/menu_style.png

And if you want to run only a cnn function, please execute:

::

    $ feedy main.py app --max-entries 2 --no-ignore-fetched --target cnn
    http://i.cdn.turner.com/cnn/.e1mo/img/4.0/logos/menu_money.png
    http://i.cdn.turner.com/cnn/.e1mo/img/4.0/logos/menu_style.png


After that, please execute a following command:


4. Use plugins
--------------

You can easy developing by using plugins.
For example, you can get shared count in social sns like facebook and pocket.
There are two ways for applying the plugin.

**apply specified function using decorator**

.. code-block:: python

    from feedy_plugins import social_share_plugin

    @app.add('http://rss.cnn.com/rss/edition.rss')
    @social_share_plugin
    def cnn_shared(feed_info, entry_info, body, social_count):
        article = {
            'title': entry_info['title'],
            'pocket': social_count['pocket_count'],
            'facebook': social_count['facebook_count'],
        }
        print(article)


And running:

::

    $ feedy main.py app -t cnn_shared -m 2
    {'title': 'Searchers locate Flight 804, EgyptAir vice chairman says', 'pocket': 4, 'facebook': 25}
    {'title': 'Security fears over French airports', 'pocket': 2, 'facebook': 9}


**apply all functions with ``.install()``**

.. code-block:: python

    from feedy import Feedy
    from feedy_plugins import social_share_plugin
    from bs4 import BeautifulSoup

    app = Feedy(store='feedy.dat', ignore_fetched=True)
    app.install(social_shared_plugin)  # apply each patterns.

    @app.add('http://rss.cnn.com/rss/edition.rss')
    def cnn_shared(feed_info, entry_info, body, social_count):
        article = {
            'title': entry_info['title'],
            'pocket': social_count['pocket_count'],
            'facebook': social_count['facebook_count'],
        }
        print(article)

    @app.add('https://www.djangopackages.com/feeds/packages/latest/rss/', social_count)
    def djangopackages(feed_info, entry_info, body, social_count):
        print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))
        print(social_count['pocket_count'])

    if __name__ == '__main__':
        app.run()


==============
Create Plugins
==============

To write a new plugin, simply create decorator like:

.. code-block:: python

    def social_share_plugin(callback):
        @wraps(callback)
        def wrapper(*args, **kwargs):
            additional_info = "This is custom plugin."
            kwargs['additional_info'] = additional_info
            callback(*args, **kwargs)
        return wrapper


Happy hacking :)

=========
Resources
=========

* `Github <https://github.com/c-bata/feedy>`_
* `PyPI <https://pypi.python.org/pypi/feedy>`_
