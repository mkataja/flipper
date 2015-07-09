import logging
from random import randrange

from sqlalchemy.sql.expression import exists
from sqlalchemy.sql.functions import func

from models.markov_entry import MarkovEntry


class MarkovCorpusMissingException(ValueError):
    pass


class MarkovChain():
    SECOND_ORDER_MINIMUM_HITS = 2

    SENTENCE_LENGTH_MINIMUM = 8
    SENTENCE_LENGTH_RANDOM_PART = 4

    END_SENTENCE_REMAINING_THRESHOLD = 7
    END_SENTENCE_MINIMUM_LENGTH = 5

    def __init__(self, session, corpus_id):
        self.session = session
        if not session.query(exists().where(MarkovEntry.corpus_id == corpus_id)).scalar():
            raise MarkovCorpusMissingException("Corpus '{}' does not exist"
                                               .format(corpus_id))
        else:
            self.corpus = (self.session.query(MarkovEntry)
                           .filter_by(corpus_id=corpus_id))

    def get_sentence(self, seed):
        """
        seed -- (optional) a list of words to use as a basis for generating the sentence
        """

        if seed is None or len(seed) == 0:
            seed = [self._get_random_word()]
        else:
            if (not self._word_in_corpus(seed[0])
                and not self._word_in_corpus(seed[-1])):
                return None

        sentence_max_length = self._get_sentence_max_length() + len(seed)

        logging.debug("Markov: Creating sentence with max_length {}"
                      .format(sentence_max_length))

        sentence = filter(None, self._extend_sentence(seed, sentence_max_length))
        return ' '.join(sentence)

    def _get_random_word(self):
        random_source = (self.corpus
                         .with_entities(MarkovEntry.prev_1)
                         .group_by(MarkovEntry.prev_1)
                         .having(func.count(MarkovEntry.prev_1) > 1))
        row_count = random_source.count()

        if row_count == 0:
            random_source = self.corpus
            row_count = random_source.count()

        return random_source.offset(randrange(row_count)).first().prev_1

    def _word_in_corpus(self, word):
        matches = self.corpus.filter_by(prev_1=word)
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
        prev_1 = sentence[-1]
        if prev_1 is not None:
            prev_2 = sentence[-2] if len(sentence) > 1 else None
            next_word = self._get_next_word(prev_1, prev_2, False, prefer_nonterminal)
            sentence.append(next_word)

        # Extend sentence backward
        follow_1 = sentence[0]
        if follow_1 is not None:
            follow_2 = sentence[1] if len(sentence) > 1 else None
            next_word = self._get_next_word(follow_1, follow_2, True, prefer_nonterminal)
            sentence.insert(0, next_word)

        sentence = self._extend_sentence(sentence, max_length)
        return sentence

    def _get_next_word(self, s_0, s_1, backwards, prefer_nonterminal):
        """
        s_0 -- the nearest search predicate
        s_1 -- the second nearest search predicate (may be None)
        """

        if s_0 is None:
            return None

        filtered_attr = MarkovEntry.prev_2 if backwards else MarkovEntry.next
        if prefer_nonterminal:
            filter_expr = filtered_attr != None
        else:
            filter_expr = filtered_attr == None

        if s_1 is not None:
            if backwards:
                candidates = self.corpus.filter_by(prev_1=s_0, next=s_1)
            else:
                candidates = self.corpus.filter_by(prev_1=s_0, prev_2=s_1)

            terminal_filtered = candidates.filter(filter_expr)
            if terminal_filtered.count() > 0:
                logging.debug("Markov: Getting only {}terminal hits"
                              .format('non' if prefer_nonterminal else ''))
                candidates = terminal_filtered

            hits = candidates.count()
            logging.debug("Markov: {} second order hits for s_1={}, s_0={}: {}"
                          .format('<' if backwards else '>', s_1, s_0, hits))

        if s_1 is None or hits < MarkovChain.SECOND_ORDER_MINIMUM_HITS:
            candidates = self.corpus.filter_by(prev_1=s_0)

            terminal_filtered = candidates.filter(filter_expr)
            if terminal_filtered.count() > 0:
                logging.debug("Markov: Getting only {}terminal hits"
                              .format('non' if prefer_nonterminal else ''))
                candidates = terminal_filtered

            hits = candidates.count()
            logging.debug("Markov: {} first order hits for '{}': {}"
                          .format('<' if backwards else '>', s_0, hits))
            if hits < 1:
                return None

        selection = candidates.offset(randrange(hits)).first()
        if backwards:
            next_word = selection.prev_2
        else:
            next_word = selection.next
        return next_word
