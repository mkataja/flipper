import imp
import random
import re
import time

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
        
        import commands.builtincommands
        imp.reload(commands.builtincommands)
        
        import commands.weathercommand
        imp.reload(commands.weathercommand)
        
        import message
        message.reload_commandlist()
        
        msg.reply_to("Tehty!")


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


class RollCommand(Command):
    helpstr = "Käyttö: speksaa heitettävä noppa muodossa AdX (esim 2d6)"
    
    rolling = False
    
    def handle(self, message):
        if RollCommand.rolling:
            message.reply_to("Yksi heitto kerrallaan")
            return
        
        RollCommand.rolling = True
        try:
            self.roll(message)
        finally:
            RollCommand.rolling = False
    
    def roll(self, message):
        matches = re.match("([1-9][0-9]*)d([1-9][0-9]*)", message.params.strip())
        
        if matches is None:
            self.replytoinvalidparams(message)
            return
        
        num_dice = int(matches.group(1))
        num_faces = int(matches.group(2))
        
        if num_dice > 20:
            message.reply_to("Liikaa noppia")
            return
        
        if not 1 < num_faces <= 10000:
            message.reply_to("Nigga please, {}...".format(num_faces))
            return
        
        rolls = [random.randint(1, num_faces) for _ in range(num_dice)]
        
        if num_dice > 4:
            message.reply_to("Heitit: {}. Heittojen summa: {}"
                             .format(", ".join(map(str, rolls)),
                                     sum(rolls)))
        elif num_dice == 1:
            message.reply_to("Heitit: {}".format(rolls[0]))
        else:
            for roll in rolls:
                message.reply_to("Heitit: {}...".format(roll))
                time.sleep(2)
            message.reply_to("Heittojen summa: {}".format(sum(rolls)))
