import logging
import threading

import config
from modules.module import Module


class RepeatModule(Module):
    last = {}
    updating = threading.Lock()

    def on_pubmsg(self, connection, event):
        target = event.target.lower()
        message = event.arguments[0].strip()

        if message is None or message.startswith(config.CMD_PREFIX):
            return

        with RepeatModule.updating:
            last = self.last.get(target, None)
            logging.debug("Repeat: last: {}, current: {}".format(last, message))
            if message == last:
                self._bot.safe_privmsg(target, message)
                self.last[target] = None
            else:
                self.last[target] = message
