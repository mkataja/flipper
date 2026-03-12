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


def _cos_omega_at_jd(jd, lat):
    """Compute cos(hour-angle) at rise/set altitude for a given JD."""
    sun_data = sun_ecliptic_longitude(jd)
    decl = todeg(asin(dsin(OBLIQUITY) * dsin(sun_data['lambda_sun'])))
    return ((dsin(SUN_RISE_SET_ALTITUDE) - dsin(lat) * dsin(decl))
            / (dcos(lat) * dcos(decl)))


def sun_times(dt, lat, lon):
    """Calculate sunrise and sunset times (UTC) for a given date and location.

    Uses one iteration of refinement: initial estimates are computed from
    solar parameters at noon UT, then the hour-angle is recalculated using
    the declination at each estimated event time.  This matters near the
    polar circle where declination changes enough between noon and midnight
    to flip the sunrise/sunset existence.

    Args:
        dt: date or datetime for which to calculate
        lat: latitude in degrees (north positive)
        lon: longitude in degrees (east positive)

    Returns:
        dict with 'sunrise' and 'sunset' as datetime objects in UTC,
        or None values if the sun doesn't rise or set (polar regions).
        When both are None, 'sun_above_horizon' indicates midnight sun
        (True) vs polar night (False).
    """
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt

    jd_noon = julian_day(d)

    sun_data = sun_ecliptic_longitude(jd_noon)
    lambda_sun = sun_data['lambda_sun']

    decl = todeg(asin(dsin(OBLIQUITY) * dsin(lambda_sun)))

    ra = todeg(atan2(dcos(OBLIQUITY) * dsin(lambda_sun), dcos(lambda_sun)))
    ra = fixangle(ra)

    gmst = greenwich_mean_sidereal_time(jd_noon)

    lst = fixangle(gmst + lon)
    ha = lst - ra
    if ha > 180:
        ha -= 360
    elif ha < -180:
        ha += 360

    transit_h = 12.0 - ha / 15.0

    cos_om = ((dsin(SUN_RISE_SET_ALTITUDE) - dsin(lat) * dsin(decl))
              / (dcos(lat) * dcos(decl)))

    if cos_om > 1.0:
        return {'sunrise': None, 'sunset': None, 'sun_above_horizon': False}
    if cos_om < -1.0:
        return {'sunrise': None, 'sunset': None, 'sun_above_horizon': True}

    omega_h = todeg(acos(cos_om)) / 15.0
    rise_h_est = transit_h - omega_h
    set_h_est = transit_h + omega_h

    midnight = datetime(d.year, d.month, d.day)

    # Refine sunrise: recompute hour-angle using declination at estimated time
    sunrise = None
    cos_om_rise = _cos_omega_at_jd(jd_noon + (rise_h_est - 12.0) / 24.0, lat)
    if -1.0 <= cos_om_rise <= 1.0:
        omega_rise = todeg(acos(cos_om_rise)) / 15.0
        sunrise = midnight + timedelta(hours=transit_h - omega_rise)

    # Refine sunset: recompute hour-angle using declination at estimated time
    sunset = None
    cos_om_set = _cos_omega_at_jd(jd_noon + (set_h_est - 12.0) / 24.0, lat)
    if -1.0 <= cos_om_set <= 1.0:
        omega_set = todeg(acos(cos_om_set)) / 15.0
        sunset = midnight + timedelta(hours=transit_h + omega_set)

    if sunrise is None and sunset is None:
        return {'sunrise': None, 'sunset': None, 'sun_above_horizon': True}
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
        return f"Aurinko nousee {sr} ja yötön yö alkaa."

    if sunset and not sunrise:
        ss = time_util.utc_to_local(sunset, timezone).strftime('%H:%M')
        return f"Yötön yö loppuu - aurinko laskee {ss}."

    if result.get('sun_above_horizon'):
        return "Yötön yö eli polaaripäivä - aurinko ei laske kyseisenä päivänä."

    return "Kaamos eli polaariyö - aurinko ei nouse kyseisenä päivänä."
