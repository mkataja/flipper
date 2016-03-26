import logging
import re
import time
import unicodedata

from commands import commandlist
import config
from services.accesscontrol import has_admin_access


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
                command_start = time.time()
                command().handle(self)
                logging.info("Ran command: '{}' (with params: '{}') "
                             "(took {:.3f} s)".
                              format(self.commandword,
                                     self.params,
                                     time.time() - command_start))
            else:
                logging.warn("unrecognized command: {}".
                              format(self.commandword))

    def try_run_command(self):
        try:
            self.run_command()
        except:
            self.reply_to("Tapahtui virhe. Kerro tästä devaajille.")
            raise

    def reply_to(self, replytext):
        replytext = re.sub(r"(\r?\n|\t)+", ' ', replytext)
        replytext = ''.join(c for c in replytext if unicodedata.category(c)[0]!="C")

        if self.is_private_message:
            target = self.sender
        else:
            target = self.source
            replytext = self.sender + ": " + replytext

        self._connection.privmsg(target, replytext)
