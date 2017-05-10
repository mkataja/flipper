import re

from lib import niiloism


NICK_REGEX = re.compile(r'(?i)^[a-z_\-\[\]\\^{}|`]'
                        '[a-z0-9_\-\[\]\\^{}|`]{2,15}$')


def get_quit_message():
    try:
        message = niiloism.random_word()
    except:
        # Fallback to make sure this never fails
        message = "Quitting"
    return message


def is_valid_nick(string):
    return NICK_REGEX.match(string)
