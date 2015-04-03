import pytz

import config


def get_utc_datetime(local_naive_datetime):
    """
    Converts a local "naive" (without timezone) datetime to UTC. Takes in
    account both the configured timezone and possible DST on that timezone.
    """
    timezone = pytz.timezone(config.TIMEZONE)
    utc_datetime = timezone.localize(local_naive_datetime).astimezone(pytz.utc)
    return utc_datetime
