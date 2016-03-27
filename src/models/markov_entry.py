from sqlalchemy.sql.schema import Column, ForeignKey, Index
from sqlalchemy.sql.sqltypes import Integer, Text

from models.markov_corpus import MarkovCorpus
from models.markov_word import MarkovWord
from services import database


class MarkovEntry(database.FlipperBase):
    corpus_id = Column(Integer,
                       ForeignKey(MarkovCorpus.id, ondelete='CASCADE'),
                       nullable=False)
    sentence_identifier = Column(Text, nullable=False)
    prev2_id = Column(Integer, ForeignKey(MarkovWord.id), nullable=True)
    prev1_id = Column(Integer, ForeignKey(MarkovWord.id), nullable=False)
    next_id = Column(Integer, ForeignKey(MarkovWord.id), nullable=True)

    Index("ix_markov_entry_corpus_id_prev1_id_next_id", corpus_id, prev1_id, next_id)
    Index("ix_markov_entry_corpus_id_prev1_id_prev2_id", corpus_id, prev1_id, prev2_id)
