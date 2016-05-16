from feedy import Feedy
from bs4 import BeautifulSoup

feedy = Feedy('./feedy.dat')


@feedy.add('http://nwpct1.hatenablog.com/rss')
def c_bata_web(feed_info, entry_info, body):
    soup = BeautifulSoup(body)
    print('========================')
    print(feed_info['title'])
    print(feed_info['subtitle'])
    print(feed_info['link'])
    print(feed_info['fetched_at'])
    print(entry_info.title)
    print(entry_info.link)
    print(soup.title)


if __name__ == '__main__':
    feedy.run('all')
