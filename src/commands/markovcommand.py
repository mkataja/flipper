from commands.command import Command
from lib.markov_chain import MarkovCorpusException, MarkovChain
from models.markov_corpus import MarkovCorpus
from services import database


class MarkovCommand(Command):
    helpstr = ("Käyttö: anna aineiston nimi ensimmäisenä parametrina, "
               "halutessasi avainsanoja sen jälkeen")

    def handle(self, message):
        params = message.params.split(maxsplit=1)
        if len(params) < 1:
            self.replytoinvalidparams(message)
            return
        corpus_name = params[0]
        seed = params[1] if len(params) > 1 else ''
        message.params = seed
        command = get_markov_command(corpus_name=corpus_name)()
        command.handle(message)


class AbstractMarkovCommand(Command):
    helpstr = "Käyttö: anna halutessasi avainsanoja"
    corpus_id = None
    corpus_name = None

    def handle(self, message):
        params = message.params.split()
        seed = [w.lower() for w in params] if len(params) > 0 else None

        with database.get_session() as session:
            if self.corpus_id:
                corpus_id = self.corpus_id
            else:
                corpus_id = (session.query(MarkovCorpus.id)
                             .filter_by(name=self.corpus_name).scalar())
                if not corpus_id:
                    message.reply_to("Sanastoa {} ei löydy"
                                     .format(self.corpus_name))
                    return
            try:
                markov = MarkovChain(session, corpus_id)
            except MarkovCorpusException:
                message.reply_to("Sanasto on tyhjä")
                return
            sentence = markov.get_sentence(seed)
        if sentence is not None:
            message.reply_to((sentence[0].upper() + sentence[1:]) + '.')
        else:
            message.reply_to("Ei löydy mitään")


def get_markov_command(corpus_id=None, corpus_name=None):
    if corpus_id and corpus_name:
        raise ValueError("Both corpus_id and corpus_name given "
                         "(only one argument allowed)")
    class_name = '{}MarkovCommand'.format(corpus_name or 'Id{}'
                                          .format(corpus_id))
    return type(class_name, (AbstractMarkovCommand,), locals())
