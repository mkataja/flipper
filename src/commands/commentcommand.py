from commands.command import Command
from lib import niiloism


class CommentCommand(Command):
    def handle(self, message):
        message.reply_to(niiloism.random_word())
