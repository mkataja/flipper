from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer

from models.channel import Channel
from models.markov_corpus import MarkovCorpus
from models.user import User
from services import database


class ImitateCorpus(database.FlipperBase):
    channel_id = Column(Integer, ForeignKey(Channel.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    corpus_id = Column(Integer, ForeignKey(MarkovCorpus.id), nullable=False)

    @classmethod
    def get_or_create(cls, channel, user):
        with database.get_session() as session:
            corpus_id = (session.query(ImitateCorpus.corpus_id)
                         .filter_by(channel_id=channel.id, user_id=user.id)
                         .scalar())
            if not corpus_id:
                markov_corpus = MarkovCorpus()
                markov_corpus.name = "_imitate_{}>{}".format(channel.name, user.nick)
                session.add(markov_corpus)
                session.flush()

                imitate_corpus = ImitateCorpus()
                imitate_corpus.channel_id = channel.id
                imitate_corpus.user_id = user.id
                imitate_corpus.corpus_id = markov_corpus.id
                session.add(imitate_corpus)
                session.commit()

                corpus_id = markov_corpus.id
            return corpus_id
