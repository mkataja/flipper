'''
Created on 14.10.2013

@author: Matias
'''

from oyoyo import helpers, parse

from commands import commandlist

import logging
import re

class Message(object):
    CMD_PREFIX = "!"  # TODO lataa konfiguraatiosta
    
    commandword = None
    params = None
    
    def __init__(self, client, nickstring, source, content, is_private_message):
        self.client = client
        self.nickstring = nickstring
        parsednickstring = parse.parse_nick(nickstring) 
        self.sender = parsednickstring[0]
        self.sender_mode = parsednickstring[1]
        self.sender_user = parsednickstring[2]
        self.sender_host = parsednickstring[3]
        self.source = source
        self.content = content
        self.is_private_message = is_private_message
    
    def __str__(self):
        desc = "{}@{}: {}".format(self.sender,
                                  self.source,
                                  self.content) + \
               (" (private message)" if self.is_private_message else "")
        return desc
    
    def reply_to(self, replytext):
        if self.is_private_message:
            target = self.sender
        else:
            target = self.source
        msgtosend = (self.sender + ": " if not self.is_private_message else "") + replytext
        helpers.msg(self.client, target, msgtosend)
    
    def parse_and_run_command(self):
        '''
        True if received message could be interpreted as a command
        (regardless if the command actually exists or could be ran)
        '''
        cmd_prefix_regex = self.CMD_PREFIX + "?" if self.is_private_message else self.CMD_PREFIX
        regex = re.compile("^({}[:,\s]+|{})"
                           .format(self.client.nick, cmd_prefix_regex)
                           + "([^\s]*)\s*(.*)",
                           re.IGNORECASE)
        result = regex.search(self.content)
        if result:
            self.commandword = result.groups()[1].lower()
            self.params = result.groups()[2]
            
            allowedcommands = commandlist.PUBLIC_CMDS
            if self.is_private_message:
                allowedcommands.update(commandlist.PRIVATE_CMDS)
            
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
