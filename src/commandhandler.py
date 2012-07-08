'''
Created on Jul 7, 2012

@author: Matias
'''

from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers

import commands

import logging
import re
import imp

def reload_commands():
    imp.reload(commands)

class CommandHandler(DefaultCommandHandler):
    
    class Message(object):
        commandword = None
        params = None
        
        def __init__(self, client, sender, source, content, is_privmsg):
            self.client = client
            self.sender = sender
            self.source = source
            self.content = content
            self.is_privmsg = is_privmsg
        
        def __str__(self):
            desc = "{}@{}: {}".format(self.sender,
                                      self.source,
                                      self.content) + \
                   (" (private message)" if self.is_privmsg else "")
            return desc
        
        def replyto(self, replytext):
            if self.is_privmsg:
                target = self.sender
            else:
                target = self.source
            msgtosend = (self.sender + ": " if not self.is_privmsg else "") + replytext
            helpers.msg(self.client, target, msgtosend)
        
        def parse_and_run_command(self):
            '''
            True if received message could be interpreted as a command
            (regardless if the command actually exists or could be ran)
            '''
            CMD_PREFIX = "!"
            cmd_prefix = CMD_PREFIX + "?" if self.is_privmsg else CMD_PREFIX
            regex = re.compile("^({}[:,\s]+|{})".
                               format(self.client.nick, cmd_prefix) + 
                               "([^\s]*)\s*(.*)",
                               re.IGNORECASE)
            result = regex.search(self.content)
            if result:
                self.commandword = result.groups()[1].lower()
                self.params = result.groups()[2].lower()
                
                allowedcommands = commands.PUBLIC_CMDS
                if self.is_privmsg:
                    allowedcommands.update(commands.PRIVATE_CMDS)
                if self.commandword in allowedcommands:
                    command = allowedcommands[self.commandword]
                    command().handle(self)
                    logging.debug("ran command: '{}' (with params: '{}')".
                                  format(self.commandword, self.params))
                else:
                    logging.debug("unrecognized/unallowed command: {}".
                                  format(self.commandword))
                return True
            else:
                return False
    
    
    def create_message(self, sender, source, content, is_privmsg):
        return self.Message(self.client, sender, source, content, is_privmsg)
    
    def privmsg(self, nickstring, message_source, msg):
        sender_nick = nickstring.decode().split("!")[0]
        message_content = msg.decode()
        message_source = message_source.decode()
        if message_source.lower() == self.client.nick.lower():
            is_privmsg = True
        else:
            is_privmsg = False
        message = self.create_message(sender_nick,
                                      message_source,
                                      message_content,
                                      is_privmsg)
        logging.debug("handling privmsg: {}".format(message))
        message.parse_and_run_command()
