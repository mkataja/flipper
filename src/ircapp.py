#!/usr/bin/python
'''
Created on Jul 4, 2012

@author: Matias
'''

from oyoyo.client import IRCClient, IRCApp
import commandhandler

import logging
import yaml

class IRCBot(IRCApp):
    
    class Config(object):
        def __init__(self, conf_file):
            conf_yaml = yaml.load(open(conf_file, "r"))
            self.server = conf_yaml["server"]
            self.port = conf_yaml["port"]
            self.nick = conf_yaml["nick"]
            self.channels = conf_yaml["channels"]
    
    
    def __init__(self):
        IRCApp.__init__(self)
        self.config = self.Config("../config/flipper.conf")
        client = IRCClient(commandhandler.CommandHandler, 
                           host=self.config.server, 
                           port=self.config.port, 
                           nick=self.config.nick,  
                           blocking=True)
        client.command_handler.channels_to_join = self.config.channels
        self.addClient(client, autoreconnect=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    botinstance = IRCBot()
    botinstance.run()
