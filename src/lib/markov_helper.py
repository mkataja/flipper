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

def insert_markov_sentences(sentences, corpus_id, text_identifier):
    with database.get_session() as session:
        for i, sentence in enumerate(sentences):
            sentence_identifier = '{}_{}'.format(text_identifier, i)
            word_ids = [MarkovWord.get_or_create(word) for word in sentence]
            for previous, current, following in previous_and_next(word_ids):
                entry = MarkovEntry()
                entry.corpus_id = corpus_id
                entry.sentence_identifier = sentence_identifier
                entry.prev2_id = previous
                entry.prev1_id = current
                entry.next_id = following
                session.add(entry)
            session.commit()
