'''
Created on 14.10.2014

@author: Matias
'''

from commands.command import Command, admin_required

from oyoyo import helpers
import random
import re
import imp


class HelpCommand(Command):
    def handle(self, message):
        if not message.params:
            self.replytoinvalidparams(message)
        from commands.commandlist import PRIVATE_CMDS, PUBLIC_CMDS
        allcommands = PUBLIC_CMDS.copy()
        allcommands.update(PRIVATE_CMDS)
        if message.params in allcommands:
            command = allcommands[message.params]
            message.reply_to(command.helpstr)
        else:
            message.reply_to("Tuntematon komento '{}'".format(message.params))


class ListCommand(Command):
    def handle(self, message):
        from commands.commandlist import PRIVATE_CMDS, PUBLIC_CMDS
        allcommands = PUBLIC_CMDS.copy()
        allcommands.update(PRIVATE_CMDS)
        message.reply_to("Komennot: {}".format(', '.join(sorted(allcommands.keys()))))
        

class ReloadCommand(Command):
    @admin_required
    def handle(self, message):
        message.reply_to("Päivitetään komennot...")
        # TODO tee kunnolla:
        import commandhandler
        commandhandler.reload_commandlist()
        message.reply_to("Tehty!")


class QuitCommand(Command):
    @admin_required
    def handle(self, message):
        helpers.quit(message.client, "kthxbye")


class JoinCommand(Command):
    @admin_required
    def handle(self, message):
        if re.match("(#|!)\w+", message.params):
            helpers.join(message.client, message.params) #@UndefinedVariable IGNORE:E1101
        else:
            self.replytoinvalidparams(message)


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
        helpers.part(message.client, channel_to_part) #@UndefinedVariable IGNORE:E1101


class FlipCommand(Command):
    helpstr = "Käyttö: anna vaihtoehdot (1...n) kauttaviivoilla erotettuna"
    
    def handle(self, message):
        flips = message.params.split("/")
        flips = [x.strip() for x in flips if x.strip() != ""]
        if not flips:
            self.replytoinvalidparams(message)
        else:
            if len(flips) == 1:
                flips = ["Jaa", "Ei"]
            message.reply_to(random.choice(flips))


class SayCommand(Command):
    helpstr = "Käyttö: anna ensimmäisenä parametrinä kohde, sitten viesti"
    
    @admin_required
    def handle(self, message):
        params = message.params.split(" ", 1)
        if len(params) != 2:
            self.replytoinvalidparams(message)
        else:
            target = params[0]
            msg = params[1]
            helpers.msg(message.client, target, msg)


class RealWeatherCommand(Command):
    def handle(self, message):
        weathers = ["Aurinko paistaa ja kaikilla on kivaa :)))",
                    "Lunta sataa ja kaikkia vituttaa.",
                    "Sää jatkuu sateisena koko maassa."]
        message.reply_to(random.choice(weathers))
