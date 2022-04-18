import logging
import re
import time

import config
from commands import commandlist
from models.channel import Channel
from models.user import User


class Message(object):
    def __init__(self, bot, connection, event, is_private_message):
        self._connection = connection
        self._event = event
        self.bot = bot

        self.sender = event.source.nick
        self.sender_user = event.source.user
        self.source = event.target
        self.content = event.arguments[0]
        self.is_private_message = is_private_message

        self.channel = Channel.get_or_create(self.source)
        self.user = User.get_or_create(self.sender)

        self.commandword, self.params, self.command = self._parse_command()

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
            commandword = result.groups()[1].lower()
            params = result.groups()[2]
            all_commands = commandlist.ALL_CMDS
            if commandword in all_commands:
                return commandword, params, all_commands[commandword]
            else:
                logging.warning(f"Unrecognized command: {commandword}")
                return commandword, params, None
        else:
            return None, None, None

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
