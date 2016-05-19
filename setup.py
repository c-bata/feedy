import os
from setuptools import setup

setup(
    name='feedy',
    version='0.0.2',
    author='Masashi Shibata <contact@c-bata.link>',
    author_email='contact@c-bata.link',
    url='https://github.com/c-bata/feedy',
    description='Simple RSS feed fetching framework',
    license='MIT License',
    keywords='rss feed',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=['feedy_plugins'],
    py_modules=['feedy'],
    entry_points={
        'console_scripts': ['feedy = feedy:cmd']
    },
    install_requires=['feedparser', 'beautifulsoup4', 'click', 'requests'],
    include_package_data=True,
    test_suite="tests",
)
