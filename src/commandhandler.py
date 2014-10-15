'''
Created on Jul 7, 2012

@author: Matias
'''

from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers

from commands import commandlist
import message

import logging
import imp

def reload_commandlist():
    imp.reload(commandlist)

class CommandHandler(DefaultCommandHandler):
    def create_message(self, sender, source, content, is_private_message):
        return message.Message(self.client, sender, source, content, is_private_message)
    
    def welcome(self, nickstring, msg_source, msg):
        # Try to join all the channels only after receiving the welcome event 
        # from the server
        for channel in self.channels_to_join:
            helpers.join(self.client, channel) #@UndefinedVariable IGNORE:E1101
    
    def notice(self, nickstring, msg_source, msg):
        pass
    
    def privmsg(self, nickstring, msg_source, msg_content):
        # A message was sent either on a channel or as a private message:
        is_private_message = (msg_source.decode().lower() == self.client.nick.lower())
        
        message = self.create_message(nickstring.decode(),
                                      msg_source.decode(),
                                      msg_content.decode(),
                                      is_private_message)
        
        logging.debug("handling privmsg: {}".format(message))
        
        message.run_command()
