import unittest

from irc.client import NickMask

from commands import commandlist
import config
from tests.test_utility import FakeBot, FakeConnection, FakeEvent, FakeMessage


ALL_COMMANDS = dict(list(commandlist.PRIVATE_CMDS.items()) + 
                    list(commandlist.PUBLIC_CMDS.items()))


class _TestCommand(unittest.TestCase):
    commandToRun = None
    is_privmsg = None
    source = None
    
    def setUp(self):
        nickmask = "{}!{}@cloak-A066884E.dhcp.inet.fi".format(
            config.SUPERUSER_NICK, config.SUPERUSER_NAME)
        
        is_privmsg = self.is_privmsg
        
        bot = FakeBot()
        
        connection = FakeConnection()
        
        source = NickMask(nickmask)
        target = self.source
        arguments = [ "" ]
        event = FakeEvent(source, target, arguments)
        
        self.message = FakeMessage(bot, connection, event, is_privmsg)
        self.command = ALL_COMMANDS[self.commandToRun]


class PublicTestCommand(_TestCommand):
    is_privmsg = False
    source = "#test"


class PrivateTestCommand(_TestCommand):
    is_privmsg = True
    source = "otus"


class TestFlip(PublicTestCommand):
    commandToRun = "flip"

class TestFlipOneOption(TestFlip):
    def runTest(self):
        self.message.content = "!flip tset"
        self.message.run_command()
        assert (self.message._connection.reply == "otus: Jaa" 
                or self.message._connection.reply == "otus: Ei")
        self.assertEqual(self.message._connection.target, "#test")

class TestFlipTwoOptions(TestFlip):
    def runTest(self):
        self.message.content = "!flip test/tset"
        self.message.run_command()
        assert (self.message._connection.reply == "otus: test" 
                or self.message._connection.reply == "otus: tset")
        self.assertEqual(self.message._connection.target, "#test")

class TestFlipExtraDashes(TestFlip):
    def runTest(self):
        self.message.content = "!flip ///////test//////tset///////// /////"
        self.message.run_command()
        assert (self.message._connection.reply == "otus: test" 
                or self.message._connection.reply == "otus: tset")
        self.assertEqual(self.message._connection.target, "#test")

class TestFlipNoOptions(TestFlip):
    def runTest(self):
        self.message.content = "!flip               "
        self.message.run_command()
        self.assertEqual(self.message._connection.reply,
                         "otus: Virheelliset parametrit. Käyttö: anna vaihtoehdot (1...n) kauttaviivoilla erotettuna")
        self.assertEqual(self.message._connection.target, "#test")
        
class TestFlipNoOptionsDashes(TestFlip):
    def runTest(self):
        self.message.content = "!flip ///////  /////////   / "
        self.message.run_command()
        self.assertEqual(self.message._connection.reply,
                         "otus: Virheelliset parametrit. Käyttö: anna vaihtoehdot (1...n) kauttaviivoilla erotettuna")
        self.assertEqual(self.message._connection.target, "#test")


class TestSay(PrivateTestCommand):
    commandToRun = "say"

class TestSayToNick(TestSay):
    def runTest(self):
        self.message.content = "!say otus jotain juttuja"
        self.message.run_command()
        self.assertEqual(self.message._connection.reply, "jotain juttuja")
        self.assertEqual(self.message._connection.target, "otus")

class TestSayToChannel(TestSay):
    def runTest(self):
        self.message.content = "!say #jea jotain juttuja"
        self.message.run_command()
        self.assertEqual(self.message._connection.reply, "jotain juttuja")
        self.assertEqual(self.message._connection.target, "#jea")

class TestSayToChannelUnauthorized(TestSay):
    def runTest(self):
        self.message._event.source = NickMask("otus!not-otus@cloak-A066884E.dhcp.inet.fi")
        self.message.content = "!say #jea jotain juttuja"
        self.message.run_command()
        assert(self.message._connection.reply == "OH BEHAVE, otus"
               or self.message._connection.reply == "Oletpa tuhma poika, otus"
               or self.message._connection.reply == "Sinulla ei ole OIKEUTTA, otus")
        self.assertEqual(self.message._connection.target, self.message.sender)


class TestHelp(PublicTestCommand):
    commandToRun = "help"

class TestHelpOnSay(TestHelp):
    def runTest(self):
        self.message.content = "!help say"
        self.message.run_command()
        self.assertEqual(self.message._connection.reply, "otus: Käyttö: anna ensimmäisenä parametrinä kohde, sitten viesti")

class TestHelpOnReload(TestHelp):
    def runTest(self):
        self.message.content = "!help reload"
        self.message.run_command()
        self.assertEqual(self.message._connection.reply, "otus: Tämän komennon käyttöön ei ole ohjeita.")


class TestWeather(PublicTestCommand):
    commandToRun = "sää"

class TestWeatherDefault(TestWeather):
    def runTest(self):
        self.message.content = "!sää"
        self.message.run_command()
        self.assertEqual(self.message._connection.reply[:21], "otus: Sää Espoo (FI) ")
        
class TestWeatherFail(TestWeather):
    def runTest(self):
        self.message.content = "!sää Uasfkjasfdljfsdl"
        self.message.run_command()
        self.assertEqual(self.message._connection.reply, "otus: Paikkakunnalla Uasfkjasfdljfsdl ei ole säätä")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
