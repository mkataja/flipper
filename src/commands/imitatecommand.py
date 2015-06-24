from commands.command import Command
from commands.markovcommand import markov_command_factory


class ImitateCommand(Command):
    helpstr = ("Käyttö: anna imitoitavan nick ensimmäisenä parametrina, "
               "halutessasi avainsanoja sen jälkeen")    
    def handle(self, message):
        params = message.params.split(maxsplit=1)
        if len(params) < 1:
            self.replytoinvalidparams(message)
            return
        corpus_id = 'imitate_{}'.format(params[0])
        seed = params[1] if len(params) > 1 else ''
        message.params = seed
        command = markov_command_factory(corpus_id)
        command().handle(message)
