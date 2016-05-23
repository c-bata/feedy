from feedy import Feedy
from feedy_plugins import social_share_plugin
from bs4 import BeautifulSoup

feedy = Feedy('feedy.dat')


@feedy.add('http://rss.cnn.com/rss/edition.rss')
def cnn(feed_info, entry_info, body):
    soup = BeautifulSoup(body, "html.parser")
    for x in soup.find_all('img'):
        print(x['src'])


@feedy.add('http://rss.cnn.com/rss/edition.rss')
@social_share_plugin
def cnn_shared(feed_info, entry_info, body, social_count):
    article = {
        'url': entry_info['link'],
        'title': entry_info['title'],
        'pocket': social_count['pocket_count'],
        'facebook': social_count['facebook_count'],
    }
    print(article)


@feedy.add('https://www.djangopackages.com/feeds/packages/latest/rss/')
def djangopackages(feed_info, entry_info, body):
    print("- [{pkgname}]({link})".format(pkgname=entry_info['title'], link=entry_info['link']))

if __name__ == '__main__':
    feedy.run()
