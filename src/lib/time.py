import json
import logging
import time
import urllib

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


def get_time_in_timezone(time, timezone_id):
    """
    Converts the given timezone aware time into another timezone's local time.
    """
    timezone = pytz.timezone(timezone_id)
    return time.astimezone(timezone)


def get_geographic_timezone(latitude, longitude, timestamp=int(time.time())):
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
    try:
        reply = urllib.request.urlopen(url, timeout=3).read().decode()
    except urllib.error.HTTPError:
        return None

    data = json.loads(reply)
    if data is None:
        return None

    status = data.get('status')
    if status is None or status != 'OK':
        return None

    timezone_id = data.get('timeZoneId')
    return timezone_id
