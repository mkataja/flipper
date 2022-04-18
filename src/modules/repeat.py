import logging
import threading

import config
from modules.module import Module

REPEAT_LIMIT = 8


class RepeatModule(Module):
    last = {}
    updating = threading.Lock()

    def on_pubmsg(self, _connection, event):
        target = event.target.lower()
        message = event.arguments[0].strip()

        if message is None or len(message) > REPEAT_LIMIT or message.startswith(config.CMD_PREFIX):
            return

        with RepeatModule.updating:
            last = self.last.get(target, None)
            logging.debug("Repeat: last: {}, current: {}".format(last, message))
            if message == last:
                self._bot.privmsg(target, message)
                self.last[target] = None
            else:
                self.last[target] = message
