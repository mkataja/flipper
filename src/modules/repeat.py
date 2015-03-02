from modules.module import Module


class RepeatModule(Module):
    last = {}
    
    def on_pubmsg(self, connection, event):
        target = event.target
        message = event.arguments[0].strip()
        last = self.last.get(target, None)
        if message == last:
            self._bot.safe_privmsg(target, message)
            self.last[target] = None
        else:
            self.last[target] = message
