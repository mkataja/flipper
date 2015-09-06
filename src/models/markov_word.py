from sqlalchemy.sql.schema import Column, UniqueConstraint
from sqlalchemy.sql.sqltypes import Text

from services import database


class MarkovWord(database.FlipperBase):
    text = Column(Text, nullable=False)

    UniqueConstraint(text)

    @classmethod
    def get_or_create(cls, word_text):
        with database.get_session() as session:
            word_id = session.query(MarkovWord.id).filter_by(text=word_text).scalar()
            if not word_id:
                word = MarkovWord()
                word.text = word_text
                session.add(word)
                session.commit()
                word_id = word.id
            return word_id
