'''
Created on 9.12.2014

@author: Matias
'''

import logging

from irc import bot

import config
from message import Message


class FlipperBot(bot.SingleServerIRCBot):
    def __init__(self):
        bot.SingleServerIRCBot.__init__(self, 
                                        [(config.SERVER, config.PORT)], 
                                        config.NICK, 
                                        config.REALNAME,
                                        config.RECONNECTION_INTERVAL)
    
    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")
    
    def on_welcome(self, connection, event):
        for channel in config.CHANNELS:
            connection.join(channel)
        
    def on_privmsg(self, connection, event):
        self._handle_command(connection, event, True)
        
    def on_pubmsg(self, connection, event):
        self._handle_command(connection, event, False)
    
    def _handle_command(self, connection, event, is_private_message):
        message = Message(connection, event, is_private_message)
        
        logging.debug("handling privmsg: {}".format(message))
        
        message.run_command()
