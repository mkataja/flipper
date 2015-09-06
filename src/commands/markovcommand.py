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
        corpus_id = params[0]
        seed = params[1] if len(params) > 1 else ''
        message.params = seed
        command = get_markov_command_by_corpus_name(corpus_id)()
        try:
            command.handle(message)
        except MarkovCorpusException:
            message.reply_to("Sanastoa {} ei löydy".format(corpus_id))


class AbstractMarkovCommand(Command):
    helpstr = "Käyttö: anna halutessasi avainsanoja"

    def handle(self, message):
        params = message.params.split()
        seed = [w.lower() for w in params] if len(params) > 0 else None

        with database.get_session() as session:
            try:
                corpus_id = self.corpus_id
            except AttributeError:
                corpus_id = (session.query(MarkovCorpus.id)
                             .filter_by(name=self.corpus_name).scalar())
                if not corpus_id:
                    raise MarkovCorpusException("Corpus '{}' does not exist".format(corpus_id))
            markov = MarkovChain(session, corpus_id)
            sentence = markov.get_sentence(seed)
        if sentence is not None:
            message.reply_to((sentence[0].upper() + sentence[1:]) + '.')
        else:
            message.reply_to("Ei löydy mitään")


def get_markov_command_by_corpus_name(corpus_name):
    return type('{}MarkovCommand'.format(corpus_name),
                (AbstractMarkovCommand,),
                {'corpus_name': corpus_name})

def get_markov_command_by_corpus_id(corpus_id):
    return type('Id{}MarkovCommand'.format(corpus_id),
                (AbstractMarkovCommand,),
                {'corpus_id': corpus_id})
