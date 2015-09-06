import re

from lib.iteration import previous_and_next
from models.markov_corpus import MarkovCorpus
from models.markov_entry import MarkovEntry
from models.markov_word import MarkovWord
from services import database


WORD_MIN_LENGTH = 2
WORD_MAX_LENGTH = 31


def _is_valid_word(w):
    return len(w) >= WORD_MIN_LENGTH and len(w) <= WORD_MAX_LENGTH

def parse_markov_sentences(input_text):
    """
    Parses the input into properly sanitized sentences compliant with
    the bot's Markov chain implementation.
    """
    url_regex = '(?:(?:https?:\/\/)|www\.)(?:(?:[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)|(?:[a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+)(?::[0-9]+)?(?:(?:\/|\?)[^ "]*[^ ,;\.:">)])?'
    input_text = re.sub(url_regex, '', input_text, re.IGNORECASE)
    input_text = re.sub('[^ .!?\w-]', '', input_text)
    input_text = input_text.lower()
    sentences = [[w for w in s.split() if _is_valid_word(w)]
                 for s in re.split('[.!?]', input_text)]
    sentences = [s for s in sentences if len(s) > 1]
    return sentences

def get_or_create_corpus(corpus_name):
    with database.get_session() as session:
        corpus_id = session.query(MarkovCorpus.id).filter_by(name=corpus_name).scalar()
        if not corpus_id:
            corpus = MarkovCorpus()
            corpus.name = corpus_name
            session.add(corpus)
            session.commit()
            corpus_id = corpus.id
        return corpus_id

def get_or_create_word(word_text):
    with database.get_session() as session:
        word_id = session.query(MarkovWord.id).filter_by(text=word_text).scalar()
        if not word_id:
            word = MarkovWord()
            word.text = word_text
            session.add(word)
            session.commit()
            word_id = word.id
        return word_id

def insert_markov_sentences(sentences, corpus_name, text_identifier):
    with database.get_session() as session:
        corpus_id = get_or_create_corpus(corpus_name)
        for i, sentence in enumerate(sentences):
            sentence_identifier = '{}_{}'.format(text_identifier, i)
            word_ids = [get_or_create_word(word) for word in sentence]
            for previous, current, following in previous_and_next(word_ids):
                entry = MarkovEntry()
                entry.corpus_id = corpus_id
                entry.sentence_identifier = sentence_identifier
                entry.prev2_id = previous
                entry.prev1_id = current
                entry.next_id = following
                session.add(entry)
            session.commit()
