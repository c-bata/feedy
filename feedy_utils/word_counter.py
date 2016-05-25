from collections import Counter

from bs4 import BeautifulSoup
from janome.tokenizer import Tokenizer

tokenizer = Tokenizer()


def _get_proper_nouns(text):
    return [token.surface for token in tokenizer.tokenize(text)
            if token.part_of_speech.startswith('名詞,固有名詞') or
            token.part_of_speech.startswith('名詞,一般')]


def count_words(body):
    word_counter = Counter()
    soup = BeautifulSoup(body, "html.parser")
    for child_tag in soup.find('body').findChildren():
        if child_tag.name == 'script':
            continue
        child_text = child_tag.text
        for line in child_text.split('\n'):
            line = line.rstrip().lstrip()
            words = _get_proper_nouns(line)
            if words:
                word_counter.update(words)
    return word_counter
