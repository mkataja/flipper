import logging
from random import randrange

from sqlalchemy.sql.functions import func

from lib.markov_helper import get_or_create_word
from models.markov_corpus import MarkovCorpus
from models.markov_entry import MarkovEntry
from models.markov_word import MarkovWord


class MarkovCorpusException(ValueError):
    pass


class MarkovChain():
    SECOND_ORDER_MINIMUM_HITS = 2

    SENTENCE_LENGTH_MINIMUM = 8
    SENTENCE_LENGTH_RANDOM_PART = 4

    END_SENTENCE_REMAINING_THRESHOLD = 7
    END_SENTENCE_MINIMUM_LENGTH = 5

    def __init__(self, session, corpus_name):
        self.session = session
        corpus_id = session.query(MarkovCorpus.id).filter_by(name=corpus_name).scalar()
        if not corpus_id:
            raise MarkovCorpusException("Corpus '{}' does not exist".format(corpus_id))
        self.corpus = (self.session.query(MarkovEntry).filter_by(corpus_id=corpus_id))
        if self.corpus.count() == 0:
            raise MarkovCorpusException("Corpus '{}' is empty".format(corpus_id))

    def get_sentence(self, seed_words):
        """
        seed_words -- (optional) a list of words to use as a basis for 
                      generating the sentence
        """

        if seed_words is None or len(seed_words) == 0:
            seed_ids = [self._get_random_word_id()]
        else:
            seed_ids = [get_or_create_word(word) for word in seed_words]
            if (not self._word_id_in_corpus(seed_ids[0])
                and not self._word_id_in_corpus(seed_ids[-1])):
                return None

        sentence_max_length = self._get_sentence_max_length() + len(seed_ids)

        logging.debug("Markov: Creating sentence with max_length {}"
                      .format(sentence_max_length))

        word_ids = filter(None, self._extend_sentence(seed_ids, sentence_max_length))
        words = [self.session.query(MarkovWord).get(word_id).text for word_id in word_ids]
        return ' '.join(words)

    def _get_random_word_id(self):
        words = (self.corpus
                 .filter(MarkovEntry.prev2_id != None)
                 .filter(MarkovEntry.next_id != None))
        if words.count() == 0:
            words = (self.corpus
                     .filter((MarkovEntry.prev2_id != None)
                             | (MarkovEntry.next_id != None)))

        random_source = (words
                         .with_entities(MarkovEntry.prev1_id)
                         .group_by(MarkovEntry.prev1_id)
                         .having(func.count(MarkovEntry.prev1_id) > 1))
        row_count = random_source.count()

        if row_count == 0:
            random_source = words
            row_count = random_source.count()

        return random_source.offset(randrange(row_count)).first().prev1_id

    def _word_id_in_corpus(self, word_id):
        matches = self.corpus.filter_by(prev1_id=word_id)
        row_count = matches.count()
        return row_count > 0

    def _get_sentence_max_length(self):
        return (MarkovChain.SENTENCE_LENGTH_MINIMUM
                + randrange(MarkovChain.SENTENCE_LENGTH_RANDOM_PART)
                + randrange(MarkovChain.SENTENCE_LENGTH_RANDOM_PART))

    def _extend_sentence(self, sentence, max_length):
        if len(sentence) >= max_length:
            logging.debug("Markov: Terminating: sentence length at maximum ({}/{})"
                          .format(len(sentence), max_length))
            return sentence

        if sentence[0] is None and sentence[-1] is None:
            logging.debug("Markov: Terminating: terminals at both ends")
            return sentence

        prefer_nonterminal = True
        current_length = len(sentence)
        if (current_length > MarkovChain.END_SENTENCE_MINIMUM_LENGTH
            and current_length > max_length - MarkovChain.END_SENTENCE_REMAINING_THRESHOLD):
            prefer_nonterminal = False

        # Extend sentence forward
        prev1_id = sentence[-1]
        if prev1_id is not None:
            prev2_id = sentence[-2] if len(sentence) > 1 else None
            next_word_id = self._get_next_word_id(prev1_id, prev2_id,
                                                  False, prefer_nonterminal)
            sentence.append(next_word_id)

        # Extend sentence backward
        follow1_id = sentence[0]
        if follow1_id is not None:
            follow2_id = sentence[1] if len(sentence) > 1 else None
            next_word_id = self._get_next_word_id(follow1_id, follow2_id,
                                                  True, prefer_nonterminal)
            sentence.insert(0, next_word_id)

        sentence = self._extend_sentence(sentence, max_length)
        return sentence

    def _get_next_word_id(self, s0_id, s1_id, backwards, prefer_nonterminal):
        """
        s0_id -- the nearest search predicate
        s1_id -- the second nearest search predicate (may be None)
        """

        if s0_id is None:
            return None

        filtered_attr = MarkovEntry.prev2_id if backwards else MarkovEntry.next_id
        if prefer_nonterminal:
            filter_expr = filtered_attr != None
        else:
            filter_expr = filtered_attr == None

        if s1_id is not None:
            if backwards:
                candidates = self.corpus.filter_by(prev1_id=s0_id, next_id=s1_id)
            else:
                candidates = self.corpus.filter_by(prev1_id=s0_id, prev2_id=s1_id)

            terminal_filtered = candidates.filter(filter_expr)
            if terminal_filtered.count() > 0:
                logging.debug("Markov: Getting only {}terminal hits"
                              .format('non' if prefer_nonterminal else ''))
                candidates = terminal_filtered

            hits = candidates.count()
            logging.debug("Markov: {} second order hits for s1_id={}, s0_id={}: {}"
                          .format('<' if backwards else '>', s1_id, s0_id, hits))

        if s1_id is None or hits < MarkovChain.SECOND_ORDER_MINIMUM_HITS:
            candidates = self.corpus.filter_by(prev1_id=s0_id)

            terminal_filtered = candidates.filter(filter_expr)
            if terminal_filtered.count() > 0:
                logging.debug("Markov: Getting only {}terminal hits"
                              .format('non' if prefer_nonterminal else ''))
                candidates = terminal_filtered

            hits = candidates.count()
            logging.debug("Markov: {} first order hits for '{}': {}"
                          .format('<' if backwards else '>', s0_id, hits))
            if hits < 1:
                return None

        selection = candidates.offset(randrange(hits)).first()
        if backwards:
            next_word_id = selection.prev2_id
        else:
            next_word_id = selection.next_id
        return next_word_id
