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
            message.reply_to(f"{random.choice(taunts)}, {message.sender}")
        else:
            return fn(self, message)
    return decorated_handle


class Command:
    # Fallbacks:
    description = "Tälle komennolle ei ole kuvausta."
    helpstr = "Tämän komennon käyttöön ei ole ohjeita."

    def handle(self, message):
        logging.error(f"No handler defined for '{message.cmd}'")

    def replytoinvalidparams(self, message, elaboration=None):
        if elaboration:
            message.reply_to(f"{elaboration}. {self.helpstr}")
        else:
            message.reply_to(self.helpstr)
