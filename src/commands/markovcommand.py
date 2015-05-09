import logging
from random import randrange

from sqlalchemy.sql.expression import exists

from commands.command import Command
from models.markov_entry import MarkovEntry
from services import database


class MarkovCommand(Command):
    helpstr = "Käyttö: anna aineiston nimi ensimmäisenä parametrina, halutessasi yksi avainsana toisena"
    
    def handle(self, message):
        params = message.params.split()
        if len(params) < 1:
            self.replytoinvalidparams(message)
            return
        if len(params) > 2:
            self.replytoinvalidparams(message)
            return
        corpus_id = params[0]
        keyword = params[1] if len(params) > 1 else ''
        message.params = keyword
        command = markov_command_factory(corpus_id)
        command().handle(message)


class AbstractMarkovCommand(Command):
    helpstr = "Käyttö: anna halutessasi yksi avainsana parametrina"
    
    def handle(self, message):
        params = message.params.split()
        if len(params) > 1:
            self.replytoinvalidparams(message)
            return
        keyword = params[0] if len(params) > 0 else None
        
        with database.get_session() as session:
            try:
                markov = MarkovChain(session, self.corpus_id)
            except ValueError:
                message.reply_to("Korpusta {} ei löydy".format(self.corpus_id))
                return
            sentence = markov.get_sentence(keyword)
        if sentence is not None:
            message.reply_to((sentence[0].upper() + sentence[1:]) + '.')
        elif keyword:
            message.reply_to("Ei löydy mitään sanalla " + keyword)
        else:
            message.reply_to("Ei löydy mitään")


def markov_command_factory(corpus_id):
    return type(corpus_id + 'MarkovCommand',
                (AbstractMarkovCommand,),
                {'corpus_id': corpus_id})


class MarkovChain():
    SECOND_ORDER_MINIMUM_HITS = 2
    
    SENTENCE_LENGTH_MINIMUM = 8
    SENTENCE_LENGTH_RANDOM_PART = 4
    
    SENTENCE_END_ALGORITHM_THRESHOLD = 7
    LAST_WORDS_MINIMUM_HITS = 20
    
    def __init__(self, session, corpus_id):
        self.session = session
        if not session.query(exists().where(MarkovEntry.corpus_id == corpus_id)).scalar():
            raise ValueError("Corpus does not exist")
        else:
            self.corpus = (self.session.query(MarkovEntry)
                           .filter_by(corpus_id=corpus_id))
    
    def get_sentence(self, keyword):
        sentence_max_length = self._get_sentence_length()
        
        if keyword is None:
            keyword = self._get_random_word()
        else:
            if not self._word_in_corpus(keyword):
                return None
        
        words = []
        words.append(None)
        words.append(keyword)
        min_word_results = 1
        for i in range(sentence_max_length - 1):
            if i > sentence_max_length - MarkovChain.SENTENCE_END_ALGORITHM_THRESHOLD:
                min_word_results = MarkovChain.LAST_WORDS_MINIMUM_HITS
            prev_2 = words[i]
            prev_1 = words[i + 1]
            next_word = self._get_next_word(prev_2, prev_1, min_word_results)
            if next_word is None:
                break
            words.append(next_word)
            
        return ' '.join(words[1:])
    
    def _get_sentence_length(self):
        return (MarkovChain.SENTENCE_LENGTH_MINIMUM
                + randrange(MarkovChain.SENTENCE_LENGTH_RANDOM_PART)
                + randrange(MarkovChain.SENTENCE_LENGTH_RANDOM_PART))
    
    def _word_in_corpus(self, word):
        matches = self.corpus.filter_by(prev_1=word)
        row_count = matches.count()
        return row_count > 0
    
    def _get_random_word(self):
        row_count = self.corpus.count()
        return self.corpus.offset(randrange(row_count)).first().prev_1
    
    def _get_next_word(self, prev_2, prev_1, minimum_hits=1):
        if prev_1 is None:
            return None
        
        if prev_2 is not None:
            candidates = self.corpus.filter_by(prev_2=prev_2, prev_1=prev_1)
            hits = candidates.count()
            logging.debug("Markov: second order hits for '{} {}': {}"
                          .format(prev_2, prev_1, hits))
        if prev_2 is None or hits < MarkovChain.SECOND_ORDER_MINIMUM_HITS:
            candidates = self.corpus.filter_by(prev_1=prev_1)
            hits = candidates.count()
            logging.debug("Markov: first order hits for '{}': {}"
                          .format(prev_1, hits))
            if hits < minimum_hits:
                return None
        
        next_word = candidates.offset(randrange(hits)).first().next
        return next_word
