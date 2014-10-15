'''
Created on Jul 8, 2012

@author: Matias
'''

import unittest

from commands import commandlist
import message


ALL_COMMANDS = dict(list(commandlist.PRIVATE_CMDS.items()) + 
                    list(commandlist.PUBLIC_CMDS.items()))


class FakeClient(object):
    nick = "flipper"
    reply = None
    target = None
    
    def send(self, cli, user, msg):
        self.reply = msg[1:]
        self.target = user


class FakeMessage(message.Message):
    pass


class _TestCommand(unittest.TestCase):
    commandToRun = None
    is_privmsg = None
    source = None
    
    def setUp(self):
        nickstring = "otus!otus@cloak-A066884E.dhcp.inet.fi"
        source = self.source
        content = ""
        is_privmsg = self.is_privmsg
        self.message = FakeMessage(FakeClient(), nickstring, source, content, is_privmsg)
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
        self.message.parse_and_run_command()
        assert (self.message.client.reply == "otus: Jaa" 
                or self.message.client.reply == "otus: Ei")
        self.assertEqual(self.message.client.target, "#test")

class TestFlipTwoOptions(TestFlip):
    def runTest(self):
        self.message.content = "!flip test/tset"
        self.message.parse_and_run_command()
        assert (self.message.client.reply == "otus: test" 
                or self.message.client.reply == "otus: tset")
        self.assertEqual(self.message.client.target, "#test")

class TestFlipExtraDashes(TestFlip):
    def runTest(self):
        self.message.content = "!flip ///////test//////tset///////// /////"
        self.message.parse_and_run_command()
        assert (self.message.client.reply == "otus: test" 
                or self.message.client.reply == "otus: tset")
        self.assertEqual(self.message.client.target, "#test")

class TestFlipNoOptions(TestFlip):
    def runTest(self):
        self.message.content = "!flip               "
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, 
                         "otus: Virheelliset parametrit. Käyttö: anna vaihtoehdot (1...n) kauttaviivoilla erotettuna")
        self.assertEqual(self.message.client.target, "#test")
        
class TestFlipNoOptionsDashes(TestFlip):
    def runTest(self):
        self.message.content = "!flip ///////  /////////   / "
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, 
                         "otus: Virheelliset parametrit. Käyttö: anna vaihtoehdot (1...n) kauttaviivoilla erotettuna")
        self.assertEqual(self.message.client.target, "#test")


class TestSay(PrivateTestCommand):
    commandToRun = "say"

class TestSayToNick(TestSay):
    def runTest(self):
        self.message.content = "!say otus jotain juttuja"
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, "jotain juttuja")
        self.assertEqual(self.message.client.target, "otus")

class TestSayToChannel(TestSay):
    def runTest(self):
        self.message.content = "!say #jea jotain juttuja"
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, "jotain juttuja")
        self.assertEqual(self.message.client.target, "#jea")

class TestSayToChannelUnauthorized(TestSay):
    def runTest(self):
        self.message.sender_user = "not-otus"
        self.message.content = "!say #jea jotain juttuja"
        self.message.parse_and_run_command()
        assert(self.message.client.reply == "OH BEHAVE, otus"
               or self.message.client.reply == "Oletpa tuhma poika, otus"
               or self.message.client.reply == "Sinulla ei ole OIKEUTTA, otus")
        self.assertEqual(self.message.client.target, self.message.sender)


class TestHelp(PublicTestCommand):
    commandToRun = "help"

class TestHelpOnSay(TestHelp):
    def runTest(self):
        self.message.content = "!help say"
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, "otus: Käyttö: anna ensimmäisenä parametrinä kohde, sitten viesti")

class TestHelpOnReload(TestHelp):
    def runTest(self):
        self.message.content = "!help reload"
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, "otus: Tämän komennon käyttöön ei ole ohjeita.")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
