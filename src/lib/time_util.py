import datetime
import logging

import pytz
from timezonefinder import TimezoneFinder

import config

_TIMEZONE_FINDER = TimezoneFinder()


def get_utc_datetime(local_naive_datetime):
    """
    Converts a local "naive" (without timezone) datetime to UTC. Takes in
    account both the configured timezone and possible DST on that timezone.
    """
    timezone = pytz.timezone(config.TIMEZONE)
    utc_datetime = timezone.localize(local_naive_datetime).astimezone(pytz.utc)
    return utc_datetime


def get_time_in_timezone(time, timezone_id):
    """
    Converts the given timezone aware time into another timezone's local time.
    """
    timezone = pytz.timezone(timezone_id)
    return time.astimezone(timezone)


def get_geographic_timezone(latitude, longitude, timestamp=None):
    """
    Returns timezone id for the given geographic location (offline lookup).

    The timestamp argument is accepted for backwards compatibility but is not
    needed for coordinate-to-timezone resolution.
    """
    _ = timestamp
    if latitude is None or longitude is None:
        return None
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return None
    timezone_id = _TIMEZONE_FINDER.timezone_at(lat=latitude, lng=longitude)
    if timezone_id is None:
        logging.warning(
            f"Timezone lookup failed for coordinates lat={latitude}, lon={longitude}"
        )
        return None
    logging.info(f"Resolved timezone '{timezone_id}' for lat={latitude}, lon={longitude}")
    return timezone_id


def get_upcoming_date_for_time(time):
    if time > datetime.datetime.now().time():
        return datetime.date.today()
    else:
        return datetime.date.today() + datetime.timedelta(days=1)


def get_next_datetime_for_time(time):
    date = get_upcoming_date_for_time(time)
    return datetime.datetime.combine(date, time)


def days_until_next_weekday(weekday):
    today = datetime.date.today()
    return (weekday - today.isoweekday() - 1) % 7 + 1


def add_years(date, years):
    try:
        return date.replace(year=date.year + years)
    except ValueError:
        return (date +
                (datetime.date(date.year + years, 1, 1) -
                 datetime.date(date.year, 1, 1)))
