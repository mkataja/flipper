import logging
import threading

from modules.message_handler import MessageHandler

REPEAT_LIMIT = 8


class RepeatModule(MessageHandler):
    last = {}
    updating = threading.Lock()

    def handle(self, message):
        if not (0 < len(message.content) < REPEAT_LIMIT):
            return

        with RepeatModule.updating:
            last = self.last.get(message.source, None)
            logging.debug("Repeat: last: {}, current: {}".format(last, message.content))
            if message.content == last:
                self.last[message.source] = None
                message.reply(message.content)
            else:
                self.last[message.source] = message.content
