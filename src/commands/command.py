import logging
import random

from services.accesscontrol import has_admin_access


def admin_required(fn):
    """
    Decorator used to restrict running certain commands to admins only
    """
    def decorated_handle(self, message):
        sender = message._event.source
        if not has_admin_access(sender):
            taunts = ["OH BEHAVE",
                      "Oletpa tuhma poika",
                      "Sinulla ei ole OIKEUTTA",
                      ]
            message.reply_to("{}, {}".format(random.choice(taunts),
                                             message.sender))
        else:
            return fn(self, message)
    return decorated_handle


class Command(object):
    USAGE_ERROR = "Virheelliset parametrit."

    description = "Tälle komennolle ei ole kuvausta."
    helpstr = "Tämän komennon käyttöön ei ole ohjeita."

    def handle(self, message):
        logging.error("No handler defined for '{}'".format(message.cmd))

    def replytoinvalidparams(self, message):
        message.reply_to("{} {}".format(self.USAGE_ERROR, self.helpstr))
