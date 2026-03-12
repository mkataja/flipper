import logging
import urllib.parse

import config
from lib.http import try_json_request
from models.address_cache_entry import AddressCacheEntry
from models.user import User
from services import database


def geocode(address):
    address = address.strip().lower()

    try:
        with database.get_session() as session:
            cache_entry = (session.query(AddressCacheEntry)
                           .filter_by(address=address).first())
            if cache_entry:
                logging.info(f"Found address in cache: '{address}' ({cache_entry.latitude}, {cache_entry.longitude})")
                if cache_entry.latitude is None or cache_entry.longitude is None:
                    return None
                else:
                    return cache_entry.latitude, cache_entry.longitude
    except ValueError:
        # Database not available - no matter
        pass

    logging.info(f"Geocoding '{address}'")

    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={config.GOOGLE_API_KEY}'
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
        logging.warning(f"Geocoding failed: API returned status {status}")
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
        logging.info(f"No geocode match for address '{address}'")
        return None
    else:
        logging.info(f"Geocoded address '{address}': {latitude}, {longitude}")
        return latitude, longitude


def resolve_location(location_str, sending_user=None):
    """Return coordinates for an explicit place or configured default.

    Resolution order:
    1) Geocode `location_str` when provided.
    2) Otherwise use sending user's saved home location (if available).
    3) Fall back to `config.LOCATION`.

    Returns a `(lat, lon)` tuple, or `None` only when explicit geocoding
    was requested and no match was found.
    """
    if location_str:
        coordinates = geocode(location_str)
        if coordinates is None:
            return None
        return coordinates[0], coordinates[1]

    if sending_user:
        try:
            user = User.get_or_create(sending_user)
            if user and user.location:
                parts = user.location.split(',')
                return float(parts[0]), float(parts[1])
        except Exception:
            pass

    parts = config.LOCATION.split(',')
    return float(parts[0]), float(parts[1])


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
    return f"{int(degrees)}°{int(minutes)}'{round(seconds, 4)}\""


def lat_to_human(dd):
    degrees, minutes, seconds = decdeg_to_dms(dd)
    s = 'N' if degrees >= 0 else 'S'
    return f"{dms_to_human(abs(degrees), minutes, seconds)} {s}"


def long_to_human(dd):
    degrees, minutes, seconds = decdeg_to_dms(dd)
    s = 'E' if degrees >= 0 else 'W'
    return f"{dms_to_human(abs(degrees), minutes, seconds)} {s}"
