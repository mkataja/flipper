from commands.command import Command
from commands.markovcommand import get_markov_command_by_corpus_id
from lib.markov_chain import MarkovCorpusException
from models.channel import Channel
from models.imitate_corpus import ImitateCorpus
from models.user import User
from services import database


class ImitateCommand(Command):
    helpstr = ("Käyttö: anna imitoitavan nick ensimmäisenä parametrina, "
               "halutessasi avainsanoja sen jälkeen")
    def handle(self, message):
        params = message.params.split(maxsplit=1)
        if len(params) < 1:
            self.replytoinvalidparams(message)
            return

        channel = message._event.target
        nick = params[0]
        with database.get_session() as session:
            channel = session.query(Channel).filter_by(name=channel).first()
            user = session.query(User).filter_by(nick=nick).first()
            if not (channel and user):
                message.reply_to("Ei sanastoa nimimerkille {}".format(nick))
                return
            corpus_id = (session.query(ImitateCorpus.corpus_id)
                         .filter_by(channel_id=channel.id, user_id=user.id)
                         .scalar())

        seed = params[1] if len(params) > 1 else ''
        message.params = seed
        command = get_markov_command_by_corpus_id(corpus_id)()
        try:
            command.handle(message)
        except MarkovCorpusException:
            message.reply_to("Ei sanastoa nimimerkille {}".format(nick))
