import datetime
import logging

import lib.time
from modules.module import Module


class FirstShoutModule(Module):
    def on_welcome(self, connection, event):
        self._setup_first_new_year()
    
    def _setup_first_new_year(self):
        next_year = datetime.datetime.now().year + 1
        new_year_first = datetime.datetime(next_year, 1, 1, 0, 0, 2)
        next_shout = lib.time.get_utc_datetime(new_year_first)
        
        logging.info("Setting new year EKA shout at {}".format(next_shout))
        self._bot.reactor.execute_at(next_shout, self._message_first_new_year, ())
    
    def _message_first_new_year(self):
        for channel in self._bot.channels.keys():
            self._bot.privmsg(channel, "Hyvää uutta vuotta!")
        self._setup_first_new_year()
