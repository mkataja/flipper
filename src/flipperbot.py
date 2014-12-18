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
        
    
    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")
    
    def on_welcome(self, connection, event):
        self.reactor.execute_every(config.KEEP_ALIVE_FREQUENCY, 
                                   self._keep_alive, ())
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
    
    def on_pong(self, connection, event):
        self.last_pong = time.time()
    
    def on_privmsg(self, connection, event):
        self._handle_command(connection, event, True)
        
    def on_pubmsg(self, connection, event):
        self._handle_command(connection, event, False)
    
    def _handle_command(self, connection, event, is_private_message):
        message = Message(connection, event, is_private_message)
        
        logging.debug("handling privmsg: {}".format(message))
        
        threading.Thread(target=message.run_command).start()
