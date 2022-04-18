import logging
import re
import time

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

        self.command = self._parse_command()
        self.is_command_invocation = (self.command is not None
                                      or self.content.startswith(config.CMD_PREFIX))

    @property
    def command_name(self):
        if self.command:
            return self.command.__name__
        else:
            return "UnrecognizedCommand"

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

        regex = re.compile(r"^({}[:,\s]+|{})(\S*)\s*(.*)"
                           .format(self._connection.get_nickname(),
                                   cmd_prefix_regex),
                           re.IGNORECASE)

        result = regex.search(self.content)

        if result:
            self.commandword = result.groups()[1].lower()
            self.params = result.groups()[2]
            all_commands = commandlist.ALL_CMDS
            if self.commandword in all_commands:
                return all_commands[self.commandword]
            else:
                logging.warning("Unrecognized command: {}"
                                .format(self.commandword))
                return None
        else:
            return None

    def run_command(self):
        if self.command:
            command_start = time.time()
            self.command().handle(self)
            logging.info("Ran command: '{}' (with params: '{}') "
                         "(took {:.3f} s)"
                         .format(self.commandword,
                                 self.params,
                                 time.time() - command_start))
        else:
            raise ("Cannot run unrecognized command: {}"
                   .format(self.commandword))

    def try_run_command(self):
        if not self.command:
            return
        try:
            self.run_command()
        except Exception as e:
            logging.exception("Exception while running command '{}': {}"
                              .format(self.command.__name__, e))
            self.reply_to("Tapahtui virhe. Kerro tästä devaajille.")
            raise

    def reply_to(self, replytext):
        if not self.is_private_message:
            replytext = self.sender + ": " + replytext
        self.reply(replytext)

    def reply(self, replytext):
        if self.is_private_message:
            target = self.sender
        else:
            target = self.source
        self.bot.privmsg(target, replytext)
