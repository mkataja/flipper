from lib import niiloism
from modules.message_handler import MessageHandler


class NiiloismModule(MessageHandler):
    def handle(self, message):
        if message is not None and message.content.lower().startswith('nj'):
            word = niiloism.random_word()
            message.reply(word)
