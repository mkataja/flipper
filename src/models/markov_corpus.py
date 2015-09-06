from sqlalchemy.sql.schema import Column, UniqueConstraint
from sqlalchemy.sql.sqltypes import Text

from services import database


class MarkovCorpus(database.FlipperBase):
    name = Column(Text, nullable=False)

    UniqueConstraint(name)

    @classmethod
    def get_or_create(cls, corpus_name):
        with database.get_session() as session:
            corpus_id = session.query(MarkovCorpus.id).filter_by(name=corpus_name).scalar()
            if not corpus_id:
                corpus = MarkovCorpus()
                corpus.name = corpus_name
                session.add(corpus)
                session.commit()
                corpus_id = corpus.id
            return corpus_id
