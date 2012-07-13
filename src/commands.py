# coding=utf-8
'''
Created on Jul 7, 2012

@author: Matias
'''

import logging
import random
import sys

def user_has_permission(message):
    if message.sender != "otus":
        message.replyto("NOT U")
        return False
    else:
        return True

class _Command(object):
    USAGE_ERROR = "Virheelliset parametrit."
    
    commandword = ""
    description = "Tälle komennolle ei ole kuvausta."
    helpstr = "Tämän komennon käyttöön ei ole ohjeita."
    
    def handle(self, message):
        logging.warning("no handler defined for '{}'".format(message.cmd))
    
    def replytoinvalidparams(self, message):
        message.replyto("{} {}".format(self.USAGE_ERROR, self.helpstr))


class ReloadCommand(_Command):
    def handle(self, message):
        if user_has_permission(message):
            message.replyto("Trying to reload commands...")
            import ircapp
            ircapp.botinstance.reload_commandhandler()
            message.replyto("Done. Hope there were no errors or we're gonna come crashing down. YEEHAAW!")


#TODO: Better implementation
class QuitCommand(_Command):
    def handle(self, message):
        if user_has_permission(message):
            message.replyto("Bye")
            sys.exit()


class FlipCommand(_Command):
    helpstr = "Käyttö: anna flippausvaihtoehdot (1...n) kauttaviivoilla erotettuna"
    
    def handle(self, message):
        flips = message.params.split("/")
        flips = [x for x in flips if x]
        if not flips:
            self.replytoinvalidparams(message)
        else:
            message.replyto(random.choice(flips))


class WeatherCommand(_Command):
    def handle(self, message):
        weathers = ["Aurinko paistaa ja kaikilla on kivaa :)))",
                    "Lunta sataa ja kaikkia vituttaa"]
        message.replyto(random.choice(weathers))

PUBLIC_CMDS = {'flip': FlipCommand,
               'flippaa': FlipCommand,
               'reload': ReloadCommand,
               'quit': QuitCommand,
               'sää': WeatherCommand}

PRIVATE_CMDS = {}
