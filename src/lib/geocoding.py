import logging
import re
import string
import urllib.parse
from dataclasses import dataclass

import config
from lib.http import try_json_request
from models.address_cache_entry import AddressCacheEntry
from models.user import User
from services import database


@dataclass(frozen=True)
class LocationResolution:
    latitude: float
    longitude: float
    resolved_name: str
    source: str


def _strip_trailing_finland(name):
    if not name:
        return name
    return re.sub(r'\s*,\s*finland\s*$', '', name, flags=re.IGNORECASE).strip()


def _digits_only(text):
    return ''.join(re.findall(r'\d', text or ''))


def _fallback_display_name(query):
    normalized = ' '.join((query or '').split()).strip()
    if not normalized:
        return normalized
    return string.capwords(normalized)


def _contains_same_number(query, candidate):
    candidate_digits = _digits_only(candidate)
    if not candidate_digits:
        return False
    query_digit_tokens = re.findall(r'\d+', query or '')
    candidate_digit_tokens = re.findall(r'\d+', candidate or '')
    if any(token in query_digit_tokens for token in candidate_digit_tokens):
        return True
    return candidate_digits in _digits_only(query)


def _component_text(component):
    return (
        component.get('long_name')
        or component.get('longText')
        or component.get('short_name')
        or component.get('shortText')
    )


def _extract_postal_codes(first_result):
    components = (
        first_result.get('address_components')
        or first_result.get('addressComponents')
        or []
    )
    postal_codes = []
    for component in components:
        types = component.get('types') or []
        if ('postal_code' in types
                or 'postal_code_prefix' in types
                or 'postal_code_suffix' in types):
            postal = _component_text(component)
            if postal:
                postal_codes.append(postal)
    return postal_codes


def _remove_leading_postal_from_part(part, postal):
    if not part:
        return part
    escaped = re.escape(postal.strip())
    if not escaped:
        return part
    return re.sub(rf'^\s*{escaped}(?=\s+)', '', part).strip()


def _strip_postal_codes_from_formatted_name(formatted_name, postal_codes, query):
    if not formatted_name:
        return formatted_name

    parts = [part.strip() for part in formatted_name.split(',')]
    cleaned_parts = []
    for part in parts:
        part_out = part
        for postal in postal_codes:
            if _contains_same_number(query, postal):
                continue
            part_out = _remove_leading_postal_from_part(part_out, postal)
        if part_out:
            cleaned_parts.append(part_out)

    if not cleaned_parts:
        return formatted_name
    return ', '.join(cleaned_parts)


def _strip_fallback_leading_zip(name, query):
    if not name:
        return name
    match = re.match(r'^\s*(?P<prefix>[0-9][0-9 ]*[0-9])(?=\s+)(?P<rest>.+)$', name)
    if not match:
        return name

    prefix = match.group('prefix')
    rest = match.group('rest').strip()
    if len(_digits_only(prefix)) < 4:
        return name
    if not rest:
        return name
    if _contains_same_number(query, prefix):
        return name
    return rest


def _resolve_display_name(first_result, original_query):
    formatted_name = (
        first_result.get('formatted_address')
        or first_result.get('formattedAddress')
        or _fallback_display_name(original_query)
    )
    postal_codes = _extract_postal_codes(first_result)
    cleaned_name = _strip_postal_codes_from_formatted_name(
        formatted_name, postal_codes, original_query)
    cleaned_name = _strip_fallback_leading_zip(cleaned_name, original_query)
    return cleaned_name or formatted_name


def _normalize_resolved_name(resolved_name, original_query):
    normalized = resolved_name or _fallback_display_name(original_query)
    normalized = _strip_trailing_finland(normalized)
    return normalized or _fallback_display_name(original_query)


def _build_geocode_url(address_cache_key):
    language = getattr(config, 'GEOCODING_LANGUAGE', 'fi')
    return (
        "https://maps.googleapis.com/maps/api/geocode/json?"
        f"address={urllib.parse.quote(address_cache_key)}&"
        f"key={config.GOOGLE_API_KEY}&"
        f"language={urllib.parse.quote(language)}"
    )


def _get_cached_geocode_resolution(address_cache_key, original_query):
    try:
        with database.get_session() as session:
            cache_entry = (session.query(AddressCacheEntry)
                           .filter_by(address=address_cache_key).first())
            if cache_entry is None:
                return False, None

            logging.info(
                f"Found address in cache: '{address_cache_key}' "
                f"({cache_entry.latitude}, {cache_entry.longitude})"
            )
            if cache_entry.latitude is None or cache_entry.longitude is None:
                return True, None

            return True, LocationResolution(
                latitude=cache_entry.latitude,
                longitude=cache_entry.longitude,
                resolved_name=_normalize_resolved_name(
                    cache_entry.resolved_name, original_query
                ),
                source='geocode',
            )
    except ValueError:
        # Database not available - no matter
        return False, None


def _store_geocode_cache_entry(address_cache_key, latitude, longitude, resolved_name):
    try:
        with database.get_session() as session:
            cache_entry = AddressCacheEntry()
            cache_entry.address = address_cache_key
            cache_entry.latitude = latitude
            cache_entry.longitude = longitude
            cache_entry.resolved_name = resolved_name
            session.add(cache_entry)
            session.commit()
    except ValueError:
        # Database not available - still no matter
        pass


def _fetch_geocode_data(address_cache_key, original_query):
    url = _build_geocode_url(address_cache_key)
    data = try_json_request(url)
    if data is None:
        return None

    status = data.get('status')
    if status == 'OK':
        results = data.get('results')
        first_result = results[0]
        location = first_result.get('geometry').get('location')
        latitude = location.get('lat')
        longitude = location.get('lng')
        resolved_name = _resolve_display_name(first_result, original_query)
        return latitude, longitude, resolved_name
    if status == 'ZERO_RESULTS':
        return None, None, None

    logging.warning(f"Geocoding failed: API returned status {status}")
    return None


def geocode(address):
    original_query = address.strip()
    address_cache_key = original_query.lower()

    cache_hit, cached_resolution = _get_cached_geocode_resolution(
        address_cache_key, original_query
    )
    if cache_hit:
        return cached_resolution

    logging.info(f"Geocoding '{address_cache_key}'")

    geocode_data = _fetch_geocode_data(address_cache_key, original_query)
    if geocode_data is None:
        return None

    latitude, longitude, resolved_name = geocode_data
    _store_geocode_cache_entry(
        address_cache_key, latitude, longitude, resolved_name
    )

    if latitude is None or longitude is None:
        logging.info(f"No geocode match for address '{address_cache_key}'")
        return None

    resolved_name = _normalize_resolved_name(resolved_name, original_query)
    logging.info(
        f"Geocoded address '{address_cache_key}': "
        f"{latitude}, {longitude} ({resolved_name})"
    )
    return LocationResolution(
        latitude=latitude,
        longitude=longitude,
        resolved_name=resolved_name,
        source='geocode',
    )


def resolve_location(location_str, sending_user=None):
    """Resolve explicit place or default location with a displayable name.

    Resolution order:
    1) Geocode `location_str` when provided.
    2) Otherwise use sending user's saved home location (if available).
    3) Fall back to `config.LOCATION`.

    Returns `LocationResolution`, or `None` only when explicit geocoding was
    requested and no match was found.
    """
    if location_str:
        coordinates = geocode(location_str)
        if coordinates is None:
            return None
        return coordinates

    if sending_user:
        try:
            user = User.get_or_create(sending_user)
            if user and user.location:
                parts = user.location.split(',')
                latitude = float(parts[0])
                longitude = float(parts[1])
                return LocationResolution(
                    latitude=latitude,
                    longitude=longitude,
                    resolved_name=f"{latitude},{longitude}",
                    source='user_home',
                )
        except Exception:
            pass

    parts = config.LOCATION.split(',')
    latitude = float(parts[0])
    longitude = float(parts[1])
    return LocationResolution(
        latitude=latitude,
        longitude=longitude,
        resolved_name=f"{latitude},{longitude}",
        source='config_default',
    )


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
