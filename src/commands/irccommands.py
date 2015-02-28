import re

from commands.command import Command, admin_required


class QuitCommand(Command):
    @admin_required
    def handle(self, message):
        quit_message = "kthxbye"
        if message.params:
            quit_message = message.params
        
        message._connection.quit(quit_message)
        
        raise SystemExit(0)


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
        else:
            target = params[0]
            text = params[1]
            message._connection.privmsg(target, text)
