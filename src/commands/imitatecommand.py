from commands.command import Command
from commands.markovcommand import markov_command_factory, \
    MarkovCorpusMissingException


class ImitateCommand(Command):
    helpstr = ("Käyttö: anna imitoitavan nick ensimmäisenä parametrina, "
               "halutessasi avainsanoja sen jälkeen")    
    def handle(self, message):
        params = message.params.split(maxsplit=1)
        if len(params) < 1:
            self.replytoinvalidparams(message)
            return
        
        nick = params[0]
        corpus_id = 'imitate_{}'.format(nick.lower())
        seed = params[1] if len(params) > 1 else ''
        message.params = seed
        command = markov_command_factory(corpus_id)()
        try:
            command.handle(message)
        except MarkovCorpusMissingException:
            message.reply_to("Ei sanastoa nimimerkille {}".format(nick))
