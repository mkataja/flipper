import imp
import random
import re

from commands.command import Command, admin_required


class HelpCommand(Command):
    helpstr = "Käyttö: anna parametrinä komento josta haluat lisätietoja"
    
    def handle(self, message):
        if not message.params:
            self.replytoinvalidparams(message)
            return
        
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
    def handle(self, msg):
        msg.reply_to("Päivitetään komennot...")
        
        import commands.weathercommand
        imp.reload(commands.weathercommand)
        import commands.builtincommands
        imp.reload(commands.builtincommands)
        import message
        message.reload_commandlist()
        
        msg.reply_to("Tehty!")


class QuitCommand(Command):
    @admin_required
    def handle(self, message):
        message._connection.quit("kthxbye")


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
            text = params[1]
            message._connection.privmsg(target, text)


class RealWeatherCommand(Command):
    def handle(self, message):
        weathers = ["Aurinko paistaa ja kaikilla on kivaa :)))",
                    "Lunta sataa ja kaikkia vituttaa.",
                    "Sää jatkuu sateisena koko maassa."]
        message.reply_to(random.choice(weathers))
