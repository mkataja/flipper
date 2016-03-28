import datetime

from commands.command import Command
from lib import markov_helper
from models.markov_corpus import MarkovCorpus
from services import database


_reserved_words = ['new', 'list']


class MarkovTeachCommand(Command):
    helpstr = ("Käyttö: anna aineiston nimi ensimmäisenä parametrina, "
               "sen jälkeen opetettava lause. Tai anna 'new' ensimmäisenä "
               "parametrina, sen jälkeen lisättävän aineiston nimi. "
               "Tai anna list ensimmäisenä parametrina.")

    def handle(self, message):
        params = message.params.split(maxsplit=1)
        if params[0] == "list":
            self._list_corpuses(message)
            return
        if len(params) < 2:
            self.replytoinvalidparams()
        if params[0] == "new":
            corpus_name = params[1]
            self._add_corpus(message, corpus_name)
        else:
            (corpus_name, sentence) = params
            self._add_sentence(message, corpus_name, sentence)

    def _list_corpuses(self, message):
        with database.get_session() as session:
            corpus_names = (session
                            .query(MarkovCorpus.name)
                            .filter_by(user_submittable=True).all())
            if len(corpus_names) < 1:
                message.reply_to("Ei aineistoja")
                return
            message.reply_to(', '.join([r for r, in corpus_names]))

    def _add_corpus(self, message, corpus_name):
        if corpus_name in _reserved_words:
            message.reply_to(("Nimeä '{}' ei voi käyttää".format(corpus_name)))
            return
        with database.get_session() as session:
            corpus = session.query(MarkovCorpus).filter_by(name=corpus_name).first()
            if corpus is not None:
                message.reply_to("Aineisto '{}' on jo olemassa"
                                 .format(corpus_name))
                return
            MarkovCorpus.create(corpus_name, True)
            message.reply_to("Ok")

    def _add_sentence(self, message, corpus_name, sentence):
        with database.get_session() as session:
            corpus = session.query(MarkovCorpus).filter_by(name=corpus_name).first()
            if corpus is not None:
                if not corpus.user_submittable:
                    message.reply_to("Aineistoon ei voi lisätä")
                    return
            else:
                message.reply_to("Aineistoa ei ole")
                return
            text_identifier = "{}_{}".format(message.sender, datetime.datetime.now())
            markov_helper.insert_text(sentence, corpus.id, text_identifier)
            session.commit()
            message.reply_to("Ok")
