from commands.command import Command
from lib.markov_chain import MarkovCorpusException, MarkovChain
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
        command = markov_command_factory(corpus_id)()
        try:
            command.handle(message)
        except MarkovCorpusException:
            message.reply_to("Korpusta {} ei löydy".format(corpus_id))


class AbstractMarkovCommand(Command):
    helpstr = "Käyttö: anna halutessasi avainsanoja"

    def handle(self, message):
        params = message.params.split()
        seed = params if len(params) > 0 else None

        with database.get_session() as session:
            markov = MarkovChain(session, self.corpus_id)
            sentence = markov.get_sentence(seed)
        if sentence is not None:
            message.reply_to((sentence[0].upper() + sentence[1:]) + '.')
        else:
            message.reply_to("Ei löydy mitään")


def markov_command_factory(corpus_id):
    return type(corpus_id + 'MarkovCommand',
                (AbstractMarkovCommand,),
                {'corpus_id': corpus_id})
