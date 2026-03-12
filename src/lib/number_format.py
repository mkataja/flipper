import math

DEFAULT_COORDINATE_DECIMALS = 6


def truncate_float(value, decimals=DEFAULT_COORDINATE_DECIMALS):
    factor = 10**decimals
    return math.trunc(float(value) * factor) / factor


def format_decimal_degrees(value, decimals=DEFAULT_COORDINATE_DECIMALS):
    truncated = truncate_float(value, decimals)
    formatted = f"{truncated:.{decimals}f}".rstrip('0').rstrip('.')
    if formatted in {'-0', ''}:
        return '0'
    return formatted


def format_coordinate_pair(latitude, longitude, decimals=DEFAULT_COORDINATE_DECIMALS):
    return (
        f"{format_decimal_degrees(latitude, decimals)},"
        f"{format_decimal_degrees(longitude, decimals)}"
    )
