import re

from lib.iteration import previous_and_next
from models.markov_entry import MarkovEntry
from services import database


def parse_markov_sentences(input_text):
    """
    Parses the input into properly sanitized sentences compliant with
    the bot's Markov chain implementation.
    
    Fairly trivial implementation: throws away most non-word
    characters and splits sentences at [.!?].
    """
    sanitized_text = re.sub('[^ .!?\w-]', '', input_text.lower())
    sentences = re.split('[.!?]', sanitized_text)
    return sentences

def insert_markov_sentences(sentences, corpus_id, text_id):
    with database.get_session() as session:
        for i, sentence in enumerate(sentences):
            sentence_id = '{}_{}'.format(text_id, i)
            words = sentence.split()
            for previous, current, following in previous_and_next(words):
                e = MarkovEntry()
                e.corpus_id = corpus_id
                e.sentence_id = sentence_id
                e.prev_2 = previous
                e.prev_1 = current
                e.next = following
                session.add(e)
        session.commit()
