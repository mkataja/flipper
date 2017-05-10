import _thread
import re

from commands.command import Command, admin_required
from lib import irc_helpers


class QuitCommand(Command):
    @admin_required
    def handle(self, message):
        if message.params:
            get_quit_message = message.params
        else:
            get_quit_message = irc_helpers.get_quit_message()

        message.bot.disconnect(get_quit_message)
        _thread.interrupt_main()


class HopCommand(Command):
    @admin_required
    def handle(self, message):
        message.bot.jump_server()


class JoinCommand(Command):
    @admin_required
    def handle(self, message):
        if not re.match("(#|!)\w+", message.params):
            self.replytoinvalidparams(message)
            return

        message._connection.join(message.params)


class PartCommand(Command):
    @admin_required
    def handle(self, message):
        if re.match("(#|!)\w+", message.params):
            # Part the given channel
            channel_to_part = message.params
        elif not message.params and not message.is_private_message:
            # Part this channel
            channel_to_part = message.source
        else:
            self.replytoinvalidparams(message)
            return

        message._connection.part(channel_to_part)


class SayCommand(Command):
    helpstr = "Käyttö: anna ensimmäisenä parametrinä kohde, sitten viesti"

    @admin_required
    def handle(self, message):
        params = message.params.split(" ", 1)
        if len(params) != 2:
            self.replytoinvalidparams(message)
            return

        target = params[0]
        text = params[1]

        if target[0] == '!':
            channels = [k for k in message.bot.channels.keys()
                        if k.endswith(target[1:]) and k[0] == '!']
            if len(channels) == 1:
                target = channels[0]

        message.bot.privmsg(target, text)


class NickCommand(Command):
    helpstr = "Käyttö: anna nimimerkki parametrina"

    @admin_required
    def handle(self, message):
        if not irc_helpers.is_valid_nick(message.params):
            self.replytoinvalidparams(message, "Virheellinen nimimerkki")
            return
        message.bot.set_nick(message.params)


class OpCommand(Command):
    helpstr = "Käyttö: anna nimimerkki parametrina"

    @admin_required
    def handle(self, message):
        if not irc_helpers.is_valid_nick(message.params):
            self.replytoinvalidparams(message, "Virheellinen nimimerkki")
            return
        if message.is_private_message:
            message.reply_to("Komento käytettävissä vain kanavilla")
            return
        message.bot.connection.mode(message.source,
                                    "+o {}".format(message.params))
