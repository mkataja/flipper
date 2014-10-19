'''
Created on 18.10.2013

@author: Matias
'''

import logging
import random

def admin_required(fn):
    """
    Decorator used to restrict running certain commands to admins only
    """
    def decorated_handle(self, message):
        # TODO: Better authentication
        if message.sender != "otus" or message.sender_user != "otus":
            taunts = ["OH BEHAVE",
                      "Oletpa tuhma poika",
                      "Sinulla ei ole OIKEUTTA",
                      ]
            message.reply_to("{}, {}".format(random.choice(taunts), message.sender))
        else:
            return fn(self, message)
    return decorated_handle


class Command(object):
    USAGE_ERROR = "Virheelliset parametrit."
    
    description = "Tälle komennolle ei ole kuvausta."
    helpstr = "Tämän komennon käyttöön ei ole ohjeita."
    
    def handle(self, message):
        logging.debug("no handler defined for '{}'".format(message.cmd))
    
    def replytoinvalidparams(self, message):
        message.reply_to("{} {}".format(self.USAGE_ERROR, self.helpstr))
