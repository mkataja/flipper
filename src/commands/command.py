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
    USAGE_ERROR = "Virheelliset parametrit."

    description = "Tälle komennolle ei ole kuvausta."
    helpstr = "Tämän komennon käyttöön ei ole ohjeita."

    def handle(self, message):
        logging.error(f"No handler defined for '{message.cmd}'")

    def replytoinvalidparams(self, message, elaboration=None):
        if elaboration:
            usage_error = f"{self.USAGE_ERROR} {elaboration}."
        else:
            usage_error = self.USAGE_ERROR
        message.reply_to(f"{usage_error} {self.helpstr}")
