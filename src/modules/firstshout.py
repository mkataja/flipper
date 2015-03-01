import datetime
import logging

from modules.module import Module


class FirstShoutModule(Module):
    def on_welcome(self, connection, event):
        self._setup_first_new_year()
        self._setup_first_new_day()
        
    def _setup_first_new_day(self):
        tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
        tomorrow_first_second = datetime.datetime.combine(tomorrow, 
                                                          datetime.time(0, 0, 1))
        
        logging.debug("Setting new day EKA shout at {}".format(tomorrow_first_second))
        self._bot.reactor.execute_at(tomorrow_first_second, self._message_first_g6, ())
    
    def _message_first_g6(self):
        if self._bot.connection.is_connected():
            for channel in self._bot.channels.keys():
                # TODO: Get channels from DB
                if channel == "#g6":
                    self._bot.connection.privmsg(channel, "EKA")
        self._setup_first_new_day()
    
    def _setup_first_new_year(self):
        next_year = datetime.datetime.now().year + 1
        new_year_first = datetime.datetime(next_year, 1, 1, 0, 0, 1)
        logging.debug("Setting new year EKA shout at {}".format(new_year_first))
        self._bot.reactor.execute_at(new_year_first, self._message_first_new_year, ())
    
    def _message_first_new_year(self):
        if self._bot.connection.is_connected():
            for channel in self._bot.channels.keys():
                self._bot.connection.privmsg(channel, "Hyvää uutta vuotta!")
        self._setup_first_new_year()
