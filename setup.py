import os
from setuptools import setup, find_packages

BASE_PATH = os.path.dirname(__file__)
README = open(os.path.join(BASE_PATH, 'README.rst')).read()
CHANGES = open(os.path.join(BASE_PATH, 'CHANGES.rst')).read()

__author__ = 'Masashi Shibata <contact@c-bata.link>'
__version__ = '0.0.0'
__license__ = 'MIT License'
__author_email__ = 'contact@c-bata.link'
__url__ = 'https://github.com/c-bata/feedy'
__description__ = 'Decorator-based RSS Feed Fetcher for Python3'
__classifiers__ = [
    'Development Status :: 1 - Planning',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
]

setup(
    name='feedy',
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    description=__description__,
    long_description=README + '\n\n' + CHANGES,
    packages=find_packages(exclude=['test*']),
    install_requirements=[],
    keywords='rss feed',
    license=__license__,
    include_package_data=True,
)
