from lib import niiloism
from modules.module import Module


class NiiloismModule(Module):
    def on_pubmsg(self, connection, event):
        target = event.target.lower()
        message = event.arguments[0].strip()

        if message is not None and message.startswith('nj'):
            word = niiloism.random_word()
            self._bot.safe_privmsg(target, word)
