import datetime
import logging
import threading
import time

from irc import bot
import irc

import config
from message import Message
import modules.modulelist


class FlipperBot(bot.SingleServerIRCBot):
    def __init__(self):
        self.last_pong = None
        self.nick_tail = ""
        
        bot.SingleServerIRCBot.__init__(self, 
                                        [(config.SERVER, config.PORT)], 
                                        config.NICK, 
                                        config.REALNAME,
                                        config.RECONNECTION_INTERVAL)
        
        irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer
    
    def _dispatcher(self, connection, event):
        super()._dispatcher(connection, event)
        
        for module in modules.modulelist.MODULES:
            method = getattr(module, "on_" + event.type, None)
            if method is not None:
                threading.Thread(target=method, 
                                 args=(connection, event)).start()
    
    def on_welcome(self, connection, event):
        self.reactor.execute_every(config.KEEP_ALIVE_FREQUENCY, 
                                   self._keep_alive, ())
        self.reactor.execute_every(60, self._keep_nick, ())
        
        self._setup_timed_messages()
        
        for channel in config.CHANNELS:
            connection.join(channel)
        
    def _keep_alive(self):
        self.connection.ping("keep-alive")
        
        current_time = time.time()
        logging.debug("Last pong at {}, current time {}".format(self.last_pong,
                                                                current_time))
        if (self.last_pong is not None and 
                current_time > self.last_pong + config.KEEP_ALIVE_TIMEOUT):
            self.last_pong = None
            self.jump_server("Timeout")
    
    def _keep_nick(self):
        if self.nick_tail != "":
            self.nick_tail = ""
            logging.debug("Trying to change nick from {} to {}".format(
                self.connection.get_nickname(), config.NICK))
            self.connection.nick(config.NICK)
    
    def _setup_timed_messages(self):
        self._setup_first_new_year()
    
    def _setup_first_new_year(self):
        next_year = datetime.datetime.now().year + 1
        new_year_first = datetime.datetime(next_year, 1, 1, 0, 0, 1)
        self.reactor.execute_at(new_year_first, self._message_first_new_year, ())
    
    def _message_first_new_year(self):
        for channel in self.channels.keys():
            self.connection.privmsg(channel, "EKA")
        self._setup_first_new_year()
        
    def on_pong(self, connection, event):
        self.last_pong = time.time()
    
    def on_nicknameinuse(self, connection, event):
        self.nick_tail = self.nick_tail + "_"
        connection.nick(config.NICK + self.nick_tail)
        
    def on_privmsg(self, connection, event):
        self._handle_command(connection, event, True)
        
    def on_pubmsg(self, connection, event):
        self._handle_command(connection, event, False)
    
    def _handle_command(self, connection, event, is_private_message):
        message = Message(self, connection, event, is_private_message)
        
        logging.debug("handling privmsg: {}".format(message))
        
        threading.Thread(target=message.run_command).start()
