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
CIVIL_TWILIGHT_ALTITUDE = -6.0


def _cos_omega_at_jd(jd, lat, altitude):
    """Compute cos(hour-angle) at a given solar altitude for a JD."""
    sun_data = sun_ecliptic_longitude(jd)
    decl = todeg(asin(dsin(OBLIQUITY) * dsin(sun_data['lambda_sun'])))
    return ((dsin(altitude) - dsin(lat) * dsin(decl))
            / (dcos(lat) * dcos(decl)))


def _solar_event_times(dt, lat, lon, altitude, rise_key, set_key, always_above_key):
    """Calculate UTC rise/set event times for a target solar altitude.

    Uses one iteration of refinement: initial estimates are computed from
    solar parameters at noon UT, then the hour-angle is recalculated using
    the declination at each estimated event time.  This matters near the
    polar circle where declination changes enough between noon and midnight
    to flip the sunrise/sunset existence.
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

    cos_om = ((dsin(altitude) - dsin(lat) * dsin(decl))
              / (dcos(lat) * dcos(decl)))

    if cos_om > 1.0:
        return {rise_key: None, set_key: None, always_above_key: False}
    if cos_om < -1.0:
        return {rise_key: None, set_key: None, always_above_key: True}

    omega_h = todeg(acos(cos_om)) / 15.0
    rise_h_est = transit_h - omega_h
    set_h_est = transit_h + omega_h

    midnight = datetime(d.year, d.month, d.day)

    # Refine rise event: recalculate hour-angle at estimated event time
    rise = None
    cos_om_rise = _cos_omega_at_jd(jd_noon + (rise_h_est - 12.0) / 24.0, lat, altitude)
    if -1.0 <= cos_om_rise <= 1.0:
        omega_rise = todeg(acos(cos_om_rise)) / 15.0
        rise = midnight + timedelta(hours=transit_h - omega_rise)

    # Refine set event: recalculate hour-angle at estimated event time
    set_ = None
    cos_om_set = _cos_omega_at_jd(jd_noon + (set_h_est - 12.0) / 24.0, lat, altitude)
    if -1.0 <= cos_om_set <= 1.0:
        omega_set = todeg(acos(cos_om_set)) / 15.0
        set_ = midnight + timedelta(hours=transit_h + omega_set)

    if rise is None and set_ is None:
        return {rise_key: None, set_key: None, always_above_key: True}
    return {rise_key: rise, set_key: set_}


def sun_times(dt, lat, lon):
    """Calculate sunrise and sunset times (UTC) for a given date and location.

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
    return _solar_event_times(
        dt,
        lat,
        lon,
        SUN_RISE_SET_ALTITUDE,
        'sunrise',
        'sunset',
        'sun_above_horizon',
    )


def civil_twilight_times(dt, lat, lon):
    """Calculate civil twilight start/end times (UTC) for date and location."""
    return _solar_event_times(
        dt,
        lat,
        lon,
        CIVIL_TWILIGHT_ALTITUDE,
        'dawn',
        'dusk',
        'sun_above_civil_twilight',
    )


def _format_local_time(event_time, timezone):
    if not event_time:
        return None
    return time_util.utc_to_local(event_time, timezone).strftime('%H:%M')


def _format_civil_twilight_sentence(dt, lat, lon, timezone):
    twilight = civil_twilight_times(dt, lat, lon)
    dawn = _format_local_time(twilight.get('dawn'), timezone)
    dusk = _format_local_time(twilight.get('dusk'), timezone)

    if dawn and dusk:
        return f"Hämärä alkaa {dawn} ja päättyy {dusk}."
    if dawn and not dusk:
        return f"Hämärä alkaa {dawn}, eikä pääty kyseisenä päivänä."
    if dusk and not dawn:
        return f"Hämärä päättyy {dusk}, eikä ala kyseisenä päivänä."
    if twilight.get('sun_above_civil_twilight'):
        return "Hämärä jatkuu koko yön."
    return None


def format_sun_times_sentence(dt, lat, lon, timezone, include_civil_twilight=False):
    def _append_civil_twilight(sentence):
        if not include_civil_twilight:
            return sentence
        twilight_sentence = _format_civil_twilight_sentence(dt, lat, lon, timezone)
        if twilight_sentence:
            return sentence + " " + twilight_sentence
        return sentence

    result = sun_times(dt, lat, lon)
    sunrise = result.get('sunrise')
    sunset = result.get('sunset')

    if sunrise and sunset:
        sr = _format_local_time(sunrise, timezone)
        ss = _format_local_time(sunset, timezone)
        day_seconds = int((sunset - sunrise).total_seconds())
        day_h = day_seconds // 3600
        day_m = (day_seconds % 3600) // 60
        return _append_civil_twilight(
            f"Aurinko nousee {sr} ja laskee {ss} "
            f"(päivän pituus {day_h} h {day_m:02d} min)."
        )

    if sunrise and not sunset:
        sr = _format_local_time(sunrise, timezone)
        return f"Aurinko nousee {sr} ja yötön yö alkaa."

    if sunset and not sunrise:
        ss = _format_local_time(sunset, timezone)
        return _append_civil_twilight(f"Yötön yö loppuu - aurinko laskee {ss}.")

    if result.get('sun_above_horizon'):
        return "Yötön yö eli polaaripäivä - aurinko ei laske kyseisenä päivänä."

    return _append_civil_twilight(
        "Kaamos eli polaariyö - aurinko ei nouse kyseisenä päivänä."
    )
