import message


class FakeConnection(object):
    reply = None
    target = None
    nick = "flipper"
    
    def get_nickname(self):
        return self.nick
    
    def privmsg(self, target, text):
        self.reply = text
        self.target = target


class FakeEvent(object):
    def __init__(self, source, target, arguments):
        self.source = source
        self.target = target
        self.arguments = arguments


class FakeMessage(message.Message):
    pass
