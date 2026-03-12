"""
Sunrise and sunset calculations.

Uses the same Duffett-Smith / John Walker astronomical foundations
as the moon phase code (see astro.py), extended with declination
and hour angle calculations for the Sun.
"""

from datetime import datetime, timedelta
from math import acos, asin, atan2

from lib import time_util
from lib.astro import (
    OBLIQUITY,
    dcos,
    dsin,
    fixangle,
    greenwich_mean_sidereal_time,
    julian_day,
    sun_ecliptic_longitude,
    todeg,
)

# Accounts for atmospheric refraction (~0.567°) and solar disc radius (~0.266°)
SUN_RISE_SET_ALTITUDE = -0.833


def sun_times(dt, lat, lon):
    """Calculate sunrise and sunset times (UTC) for a given date and location.

    Args:
        dt: date or datetime for which to calculate
        lat: latitude in degrees (north positive)
        lon: longitude in degrees (east positive)

    Returns:
        dict with 'sunrise' and 'sunset' as datetime objects in UTC,
        or None values if the sun doesn't rise or set (polar regions).
    """
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt

    jd = julian_day(d)

    sun = sun_ecliptic_longitude(jd)
    lambda_sun = sun['lambda_sun']

    decl = todeg(asin(dsin(OBLIQUITY) * dsin(lambda_sun)))

    ra = todeg(atan2(dcos(OBLIQUITY) * dsin(lambda_sun), dcos(lambda_sun)))
    ra = fixangle(ra)

    gmst = greenwich_mean_sidereal_time(jd)

    # Hour angle of the sun at the moment corresponding to this JD (noon UT)
    lst = fixangle(gmst + lon)
    ha = lst - ra
    if ha > 180:
        ha -= 360
    elif ha < -180:
        ha += 360

    transit_ut_hours = 12.0 - ha / 15.0

    cos_omega = ((dsin(SUN_RISE_SET_ALTITUDE) - dsin(lat) * dsin(decl))
                 / (dcos(lat) * dcos(decl)))

    if cos_omega > 1.0:
        return {'sunrise': None, 'sunset': None, 'sun_above_horizon': False}
    if cos_omega < -1.0:
        return {'sunrise': None, 'sunset': None, 'sun_above_horizon': True}

    omega_hours = todeg(acos(cos_omega)) / 15.0

    midnight = datetime(d.year, d.month, d.day)
    sunrise = midnight + timedelta(hours=transit_ut_hours - omega_hours)
    sunset = midnight + timedelta(hours=transit_ut_hours + omega_hours)

    return {'sunrise': sunrise, 'sunset': sunset}


def format_sun_times_sentence(dt, lat, lon, timezone):
    result = sun_times(dt, lat, lon)
    sunrise = result.get('sunrise')
    sunset = result.get('sunset')

    if sunrise and sunset:
        sr = time_util.utc_to_local(sunrise, timezone).strftime('%H:%M')
        ss = time_util.utc_to_local(sunset, timezone).strftime('%H:%M')
        day_seconds = int((sunset - sunrise).total_seconds())
        day_h = day_seconds // 3600
        day_m = (day_seconds % 3600) // 60
        return (f"Aurinko nousee {sr} ja laskee {ss} "
                f"(päivän pituus {day_h} h {day_m:02d} min).")

    if sunrise and not sunset:
        sr = time_util.utc_to_local(sunrise, timezone).strftime('%H:%M')
        return f"Aurinko nousee {sr}, eikä laske kyseisenä päivänä."

    if sunset and not sunrise:
        ss = time_util.utc_to_local(sunset, timezone).strftime('%H:%M')
        return f"Aurinko laskee {ss}, eikä nouse kyseisenä päivänä."

    if result.get('sun_above_horizon'):
        return "Aurinko ei laske kyseisenä päivänä."

    return "Aurinko ei nouse kyseisenä päivänä."
