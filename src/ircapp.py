#!/usr/bin/python
'''
Created on Jul 4, 2012

@author: Matias
'''

from oyoyo.client import IRCClient, IRCApp
from oyoyo import helpers
import commandhandler

import logging
import yaml
import imp

botinstance = 0

class IRCBot(IRCApp):
    
    class Config(object):
        def __init__(self, conf_file):
            conf_yaml = yaml.load(open(conf_file, "r"))
            self.server = conf_yaml["server"]
            self.port = conf_yaml["port"]
            self.nick = conf_yaml["nick"]
            self.channels = conf_yaml["channels"]
    
    
    def connect_callback(self, client):
        for channel in self.config.channels:
            helpers.join(client, channel) #@UndefinedVariable IGNORE:E1101
    
    def __init__(self):
        IRCApp.__init__(self)
        self.config = self.Config("../config/flipper.conf")
        client = IRCClient(commandhandler.CommandHandler, 
                           host=self.config.server, 
                           port=self.config.port, 
                           nick=self.config.nick, 
                           connect_cb=self.connect_callback, 
                           blocking=True)
        self.addClient(client, autoreconnect=True)
    
    def reload_commandhandler(self):
        imp.reload(commandhandler)
        for client in self._clients:
            client.command_handler = commandhandler.CommandHandler


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    botinstance = IRCBot()
    botinstance.run()
