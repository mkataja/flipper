#!/usr/bin/python
'''
Created on Jul 4, 2012

@author: Matias
'''

from oyoyo.client import IRCClient, IRCApp

import commandhandler
import configuration

import logging

class IRCBot(IRCApp):
    def __init__(self):
        IRCApp.__init__(self)
        
        self.conf = configuration.Configuration()
        self.conf.load("../config/flipper.conf")
        
        client = IRCClient(commandhandler.CommandHandler, 
                           host=self.conf.SERVER, 
                           port=self.conf.PORT, 
                           nick=self.conf.NICK,  
                           blocking=True)
        
        client.command_handler.channels_to_join = self.conf.CHANNELS
        
        self.addClient(client, autoreconnect=False)


def start_bot():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    while True:
        botinstance = IRCBot()
        botinstance.run()

if __name__ == '__main__':
    start_bot()
