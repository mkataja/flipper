import datetime
import logging

import lib.time_util
from modules.module import Module


class FirstShoutModule(Module):
    def __init__(self, bot):
        super().__init__(bot)
        self._setup_first_new_year()

    def _setup_first_new_year(self):
        next_year = datetime.datetime.now().year + 1
        new_year_first = datetime.datetime(next_year, 1, 1, 0, 0, 2)
        next_shout = lib.time_util.get_utc_datetime(new_year_first)

        logging.info("Setting new year EKA shout at {}".format(next_shout))
        self._bot.reactor.scheduler.execute_at(next_shout,
                                               self._message_first_new_year)

    def _message_first_new_year(self):
        for channel in self._bot.channels.keys():
            self._bot.privmsg(channel, "Hyvää uutta vuotta!")
        self._setup_first_new_year()
