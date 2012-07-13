'''
Created on Jul 8, 2012

@author: Matias
'''

import unittest
import commands

import commandhandler

ALL_COMMANDS = dict(list(commands.PRIVATE_CMDS.items()) + 
                    list(commands.PUBLIC_CMDS.items()))


class FakeClient(object):
    nick = "flipper"
    reply = None
    target = None
    
    def send(self, cli, user, msg):
        self.reply = msg[1:]
        self.target = user


class FakeMessage(commandhandler.CommandHandler.Message):
    pass


class TestCommand(unittest.TestCase):
    commandToRun = None
    
    def setUp(self):
        sender = "otus"
        source = "#test"
        content = ""
        is_privmsg = False
        self.message = FakeMessage(FakeClient(), sender, source, content, is_privmsg)
        self.command = ALL_COMMANDS[self.commandToRun]


class TestFlip(TestCommand):
    commandToRun = "flip"

class TestFlipOneOption(TestFlip):
    def runTest(self):
        self.message.content = "!flip tset"
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, "otus: tset")
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
        self.message.content = "!flip ///////test//////tset//////////"
        self.message.parse_and_run_command()
        assert (self.message.client.reply == "otus: test" 
                or self.message.client.reply == "otus: tset")
        self.assertEqual(self.message.client.target, "#test")

class TestFlipNoOptions(TestFlip):
    def runTest(self):
        self.message.content = "!flip               "
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.reply, 
                         "otus: Virheelliset parametrit. Käyttö: anna flippausvaihtoehdot (1...n) kauttaviivoilla erotettuna")
        self.assertEqual(self.message.client.target, "#test")


class TestSay(TestCommand):
    commandToRun = "say"

class TestSayToTarget(TestSay):
    def runTest(self):
        self.message.content = "!say #jea jotain juttuja"
        self.message.parse_and_run_command()
        self.assertEqual(self.message.client.target, "#jea")
        self.assertEqual(self.message.client.reply, "jotain juttuja")
