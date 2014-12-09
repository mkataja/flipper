'''
Created on 9.12.2014

@author: Matias
'''

import logging

from irc import bot

from message import Message


class FlipperBot(bot.SingleServerIRCBot):
    def __init__(self, conf):
        bot.SingleServerIRCBot.__init__(self, 
                                        [(conf.server, conf.port)], 
                                        conf.nick, 
                                        conf.nick)
        self.channels_to_join = conf.channels
    
    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")
    
    def on_welcome(self, connection, event):
        for channel in self.channels_to_join:
            connection.join(channel)
        
    def on_privmsg(self, connection, event):
        self._handle_command(connection, event, True)
        
    def on_pubmsg(self, connection, event):
        self._handle_command(connection, event, False)
    
    def _handle_command(self, connection, event, is_private_message):
        message = Message(connection, event, is_private_message)
        
        logging.debug("handling privmsg: {}".format(message))
        
        message.run_command()
