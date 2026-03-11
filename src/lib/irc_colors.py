from enum import Enum, unique


@unique
class Color(Enum):
    white = '00'
    black = '01'
    dblue = '02'
    dgreen = '03'
    red = '04'
    dred = '05'
    purple = '06'
    orange = '07'
    yellow = '08'
    green = '09'
    dcyan = '10'
    cyan = '11'
    blue = '12'
    violet = '13'
    dgrey = '14'
    grey = '15'


@unique
class ControlCode(Enum):
    bold = '\x02'
    color = '\x03'
    reset = '\x0f'


def color(string, fg_color, bg_color=None):
    if fg_color is None:
        return string
    color_code = f"{ControlCode.color.value}{fg_color.value}"
    if bg_color:
        color_code = f"{color_code},{bg_color.value}"
    return f"{color_code}{string}{ControlCode.reset.value}"


def bold(string):
    return f"{ControlCode.bold.value}{string}{ControlCode.reset.value}"
