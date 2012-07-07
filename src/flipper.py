#!/usr/bin/python
'''
Created on Jul 4, 2012

@author: Matias
'''

from oyoyo.client import IRCClient, IRCApp
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers

import logging
import yaml
import re
import random


class Flipper(IRCApp):
    
    class Config(object):
        def __init__(self, conf_file):
            self.loadconfig(conf_file)
        
        def loadconfig(self, conf_file):
            conf_yaml = yaml.load(open(conf_file, "r"))
            self.server = conf_yaml["server"]
            self.port = conf_yaml["port"]
            self.nick = conf_yaml["nick"]
            self.channels = conf_yaml["channels"]
    
    
    class CommandHandler(DefaultCommandHandler):
        def privmsg(self, nickstring, chan, msg):
            msg = msg.decode()
            nick = nickstring.decode().split("!")[0]
            if re.match("^!flip\s*", msg):
                self.handle_flip(nick, msg, chan)
        
        def handle_flip(self, nick, msg, chan):
            flips = re.sub("^!flip\s*", "", msg).split("/")
            msgtosend = "{}: {}".format(nick, random.choice(flips))
            helpers.msg(self.client, chan, msgtosend)
    
    
    def connect_callback(self, client):
        for channel in self.config.channels:
            helpers.join(client, channel) #@UndefinedVariable
    
    def __init__(self):
        super(Flipper, self).__init__()
        self.config = self.Config("../config/flipper.conf")
        client = IRCClient(self.CommandHandler, 
                           host=self.config.server, 
                           port=self.config.port, 
                           nick=self.config.nick, 
                           connect_cb=self.connect_callback, 
                           blocking=True)
        self.addClient(client, autoreconnect=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    Flipper().run()
