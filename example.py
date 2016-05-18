from feedy import Feedy
from feedy_plugins import social_share_plugin
from bs4 import BeautifulSoup

feedy = Feedy()
feedy.install(social_share_plugin)


@feedy.add('http://nwpct1.hatenablog.com/rss')
def c_bata_web(feed_info, entry_info, body, social_count):
    """Get image urls in my blog's article"""
    article = {
        'url': entry_info['link'],
        'title': entry_info['title'],
        'hatebu': social_count['hatebu_count'],
        'pocket': social_count['pocket_count'],
        'facebook': social_count['facebook_count'],
    }
    # store article
    print(article)


@feedy.add('https://www.djangopackages.com/feeds/packages/latest/rss/')
def djangopackages(feed_info, entry_info, body, **kw):
    """Get the latest django library information."""
    print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))

if __name__ == '__main__':
    feedy.run('all')
