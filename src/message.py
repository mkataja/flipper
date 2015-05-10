import imp
import logging
import re

import config
from commands import commandlist
from services.accesscontrol import has_admin_access


def reload_commandlist():
    imp.reload(commandlist)


class Message(object):
    commandword = None
    params = None
    
    def __init__(self, bot, connection, event, is_private_message):
        self._connection = connection
        self._event = event
        self.bot = bot
        
        self.sender = event.source.nick
        self.sender_user = event.source.user
        self.source = event.target
        self.content = event.arguments[0]
        self.is_private_message = is_private_message
    
    def __str__(self):
        desc = "{}@{}: {}".format(self.sender,
                                  self.source,
                                  self.content) + \
               (" (private message)" if self.is_private_message else "")
        return desc
        
    def _get_allowed_commands(self):
        allowed_commands = commandlist.PUBLIC_CMDS.copy()
        
        sender = self._event.source
        if has_admin_access(sender):
            allowed_commands.update(commandlist.PRIVATE_CMDS)
        
        return allowed_commands
    
    def _parse_command(self):
        if self.is_private_message:
            cmd_prefix_regex = re.escape(config.CMD_PREFIX) + "?"
        else:
            cmd_prefix_regex = re.escape(config.CMD_PREFIX)
        
        regex = re.compile("^({}[:,\s]+|{})"
                           .format(
                                   self._connection.get_nickname(),
                                   cmd_prefix_regex)
                           + "([^\s]*)\s*(.*)",
                           re.IGNORECASE)
        
        result = regex.search(self.content)
        
        if result:
            self.commandword = result.groups()[1].lower()
            self.params = result.groups()[2]
            return True
        else:
            return False
    
    def run_command(self):
        if self._parse_command():
            all_commands = commandlist.ALL_CMDS
            
            if self.commandword in all_commands:
                command = all_commands[self.commandword]
                command().handle(self)
                logging.info("ran command: '{}' (with params: '{}')".
                              format(self.commandword, self.params))
            else:
                logging.warn("unrecognized command: {}".
                              format(self.commandword))
    
    def reply_to(self, replytext):
        replytext = re.sub(r"(\r?\n|\t)+", " ", replytext)
        
        if self.is_private_message:
            target = self.sender
        else:
            target = self.source
            replytext = self.sender + ": " + replytext
        
        self._connection.privmsg(target, replytext)
