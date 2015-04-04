import imp

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
        
        import commands.systemcommands
        imp.reload(commands.systemcommands)
        
        import commands.openweathermapcommand
        imp.reload(commands.openweathermapcommand)
        
        import message
        message.reload_commandlist()
        
        msg.reply_to("Tehty!")
