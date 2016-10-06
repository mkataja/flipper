import re
import unicodedata

from lib.irc_colors import ControlCode


def is_allowed_character(character):
    return (character in [cc.value for cc in ControlCode] or
            unicodedata.category(character)[0] != 'C')


def sanitize(string):
    string = re.sub(r"(\r?\n|\t)+", ' ', string)
    string = ''.join(c for c in string if is_allowed_character(c))
    return string
