import datetime
import logging
import time as py_time
import urllib.parse

import pytz

import config
from lib.http import try_json_request


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


def get_geographic_timezone(latitude, longitude, timestamp=int(py_time.time())):
    """
    Returns the timezone code for the given geographic location. In case
    timestamp is given, it is used to decide between normal and daylight
    saving time. The default is to use the current timestamp to decide.
    """
    logging.info("Getting timezone for lat: {}, long: {}, at: {}"
                 .format(latitude, longitude, timestamp))

    url = ("https://maps.googleapis.com/maps/api/timezone/json?location={}&timestamp={}&key={}"
           .format(urllib.parse.quote("{},{}".format(latitude, longitude)),
                   timestamp, config.GOOGLE_API_KEY))
    data = try_json_request(url)
    if data is None:
        return None

    status = data.get('status')
    if status is None or status != 'OK':
        return None

    timezone_id = data.get('timeZoneId')
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
