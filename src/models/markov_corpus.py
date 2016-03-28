from sqlalchemy.sql.schema import Column, UniqueConstraint
from sqlalchemy.sql.sqltypes import Text, Boolean

from services import database


class MarkovCorpus(database.FlipperBase):
    name = Column(Text, nullable=False)
    user_submittable = Column(Boolean, nullable=False, default=False)

    UniqueConstraint(name)

    @classmethod
    def get_or_create(cls, corpus_name):
        with database.get_session() as session:
            corpus_id = session.query(MarkovCorpus.id).filter_by(name=corpus_name).scalar()
            if not corpus_id:
                corpus_id = MarkovCorpus.create(corpus_name)
            return corpus_id

    @classmethod
    def create(cls, corpus_name, user_submittable=False):
        with database.get_session() as session:
            corpus = MarkovCorpus()
            corpus.name = corpus_name
            corpus.user_submittable = user_submittable
            session.add(corpus)
            session.commit()
            return corpus
