import json
import logging
import urllib.parse

import config
from lib.http import try_json_request
from models.address_cache_entry import AddressCacheEntry
from services import database


def geocode(address):
    address = address.strip().lower()

    try:
        with database.get_session() as session:
            cache_entry = (session.query(AddressCacheEntry)
                           .filter_by(address=address).first())
            if cache_entry:
                logging.info("Found address in cache: '{}' ({}, {})"
                             .format(address,
                                     cache_entry.latitude,
                                     cache_entry.longitude))
                if cache_entry.latitude is None or cache_entry.longitude is None:
                    return None
                else:
                    return cache_entry.latitude, cache_entry.longitude
    except ValueError:
        # Database not available - no matter
        pass

    logging.info("Geocoding '{}'".format(address))

    url = ('https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'
           .format(urllib.parse.quote(address), config.GOOGLE_API_KEY))
    data = try_json_request(url)
    if data is None:
        return None

    status = data.get('status')
    if status == 'OK':
        results = data.get('results')
        location = results[0].get('geometry').get('location')
        latitude = location.get('lat')
        longitude = location.get('lng')
    elif status == 'ZERO_RESULTS':
        latitude = None
        longitude = None
    else:
        logging.warning("Geocoding failed: API returned status {}".format(status))
        return None

    try:
        with database.get_session() as session:
            cache_entry = AddressCacheEntry()
            cache_entry.address = address
            cache_entry.latitude = latitude
            cache_entry.longitude = longitude
            session.add(cache_entry)
            session.commit()
    except ValueError:
        # Database not available - still no matter
        pass

    if latitude is None or longitude is None:
        logging.info("No geocode match for address '{}'".format(address))
        return None
    else:
        logging.info("Geocoded address '{}': {}, {}"
                     .format(address, latitude, longitude))
        return latitude, longitude


def decdeg_to_dms(dd):
    negative = dd < 0
    dd = abs(dd)
    minutes, seconds = divmod(dd * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    if negative:
        if degrees > 0:
            degrees = -degrees
        elif minutes > 0:
            minutes = -minutes
        else:
            seconds = -seconds
    return degrees, minutes, seconds


def dms_to_human(degrees, minutes, seconds):
    return "{}°{}'{}\"".format(int(degrees), int(minutes), round(seconds, 4))


def lat_to_human(dd):
    degrees, minutes, seconds = decdeg_to_dms(dd)
    s = 'N' if degrees >= 0 else 'S'
    return "{} {}".format(dms_to_human(abs(degrees), minutes, seconds), s)


def long_to_human(dd):
    degrees, minutes, seconds = decdeg_to_dms(dd)
    s = 'E' if degrees >= 0 else 'W'
    return "{} {}".format(dms_to_human(abs(degrees), minutes, seconds), s)
