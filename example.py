from feedy import Feedy
from feedy_plugins import social_share_plugin, NewestEntryPlugin
from bs4 import BeautifulSoup

feedy = Feedy()
feedy.install(social_share_plugin)
feedy.install(NewestEntryPlugin())


@feedy.add('http://nwpct1.hatenablog.com/rss')
def c_bata_web(feed_info, entry_info, body):
    """Get image urls in my blog's article"""
    soup = BeautifulSoup(body, "html.parser")
    for x in soup.find_all('img', {'class': 'hatena-fotolife'}):
        print('-', x['src'])


@feedy.add('https://www.djangopackages.com/feeds/packages/latest/rss/')
def djangopackages(feed_info, entry_info, body):
    """Get the latest django library information."""
    print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))

if __name__ == '__main__':
    feedy.run('all')
