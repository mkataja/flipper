from commands.command import Command


class HelpCommand(Command):
    helpstr = "Käyttö: anna parametrinä komento josta haluat lisätietoja"
    
    def handle(self, message):
        if not message.params:
            self.replytoinvalidparams(message)
            return
        
        from commands.commandlist import ALL_CMDS
        if message.params in ALL_CMDS:
            command = ALL_CMDS[message.params]
            message.reply_to(command.helpstr)
        else:
            message.reply_to("Tuntematon komento '{}'".format(message.params))


class ListCommand(Command):
    def handle(self, message):
        from commands.commandlist import ALL_CMDS
        message.reply_to("Komennot: {}".format(', '.join(sorted(ALL_CMDS.keys()))))
