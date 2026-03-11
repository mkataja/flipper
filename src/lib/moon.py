# Based on moon.py, based on code by John Walker (http://www.fourmilab.ch/)
# ported to Python by Kevin Turner <acapnotic@twistedmatrix.com>
# on June 6, 2001 (JDN 2452066.52491), under a full moon.
#
# This program is in the public domain: "Do what thou wilt shall be
# the whole of the law".

"""
Functions to find the phase of the moon.

Ported from \"A Moon for the Sun\" (aka moontool.c), a program by the
venerable John Walker.  He used algoritms from \"Practical Astronomy
With Your Calculator\" by Peter Duffett-Smith, Second Edition.

For the full history of the code, as well as references to other
reading material and other entertainments, please refer to John
Walker's website,
http://www.fourmilab.ch/
(Look under the Science/Astronomy and Space heading.)
"""

from datetime import datetime, timedelta
from math import acos, asin, atan2, cos, sin

from lib.astro import (
    OBLIQUITY,
    c,
    dcos,
    dsin,
    fixangle,
    greenwich_mean_sidereal_time,
    julian_day,
    julian_day_precise,
    sun_ecliptic_longitude,
    todeg,
    torad,
)


def phase(phase_date=None):
    """Calculate phase of moon as a fraction:

    The argument is the time for which the phase is requested,
    expressed in either a DateTime or by Julian Day Number.

    Returns a dictionary containing the terminator phase angle as a
    percentage of a full circle (i.e., 0 to 1), the illuminated
    fraction of the Moon's disc, the Moon's age in days and fraction,
    the distance of the Moon from the centre of the Earth, and the
    angular diameter subtended by the Moon as seen by an observer at
    the centre of the Earth."""

    if phase_date is None:
        phase_date = datetime.now()
    jd = julian_day(phase_date)
    day = jd - c.epoch

    sun = sun_ecliptic_longitude(jd)
    lambda_sun = sun['lambda_sun']
    M = sun['M']
    sun_dist = sun['sun_dist']
    sun_angular_diameter = sun['sun_angular_diameter']

    ########
    #
    # Calculation of the Moon's position

    # Moon's mean longitude
    moon_longitude = fixangle(13.1763966 * day + c.moon_mean_longitude_epoch)

    # Moon's mean anomaly
    MM = fixangle(moon_longitude - 0.1114041 * day - c.moon_mean_perigee_epoch)

    # Moon's ascending node mean longitude
    # MN = fixangle(c.node_mean_longitude_epoch - 0.0529539 * day)

    evection = 1.2739 * sin(torad(2 * (moon_longitude - lambda_sun) - MM))

    # Annual equation
    annual_eq = 0.1858 * sin(torad(M))

    # Correction term
    A3 = 0.37 * sin(torad(M))

    MmP = MM + evection - annual_eq - A3

    # Correction for the equation of the centre
    mEc = 6.2886 * sin(torad(MmP))

    # Another correction term
    A4 = 0.214 * sin(torad(2 * MmP))

    # Corrected longitude
    lP = moon_longitude + evection + mEc - annual_eq + A4

    # Variation
    variation = 0.6583 * sin(torad(2 * (lP - lambda_sun)))

    # True longitude
    lPP = lP + variation

    #######
    #
    # Calculation of the phase of the Moon

    # Age of the Moon, in degrees
    moon_age = lPP - lambda_sun

    # Phase of the Moon
    moon_phase = (1 - cos(torad(moon_age))) / 2.0

    # Calculate distance of Moon from the centre of the Earth
    moon_dist = ((c.moon_smaxis * (1 - c.moon_eccentricity ** 2)) /
                 (1 + c.moon_eccentricity * cos(torad(MmP + mEc))))

    # Calculate Moon's angular diameter
    moon_diam_frac = moon_dist / c.moon_smaxis
    moon_angular_diameter = c.moon_angular_size / moon_diam_frac

    return {
        'phase': fixangle(moon_age) / 360.0,
        'illuminated': moon_phase,
        'age': c.synodic_month * fixangle(moon_age) / 360.0,
        'distance': moon_dist,
        'angular_diameter': moon_angular_diameter,
        'sun_distance': sun_dist,
        'sun_angular_diameter': sun_angular_diameter
    }


def moon_position(dt):
    """Compute the Moon's right ascension and declination for a datetime.

    Uses the same Duffett-Smith / moontool algorithms as phase(), extended
    with ecliptic latitude (via the ascending node) and equatorial conversion.

    Returns dict with 'ra' and 'dec' in degrees.
    """
    jd = julian_day_precise(dt)
    day = jd - c.epoch

    sun = sun_ecliptic_longitude(jd)
    lambda_sun = sun['lambda_sun']
    M = sun['M']

    moon_longitude = fixangle(13.1763966 * day + c.moon_mean_longitude_epoch)
    MM = fixangle(moon_longitude - 0.1114041 * day - c.moon_mean_perigee_epoch)
    MN = fixangle(c.node_mean_longitude_epoch - 0.0529539 * day)

    evection = 1.2739 * sin(torad(2 * (moon_longitude - lambda_sun) - MM))
    annual_eq = 0.1858 * sin(torad(M))
    A3 = 0.37 * sin(torad(M))
    MmP = MM + evection - annual_eq - A3
    mEc = 6.2886 * sin(torad(MmP))
    A4 = 0.214 * sin(torad(2 * MmP))
    lP = moon_longitude + evection + mEc - annual_eq + A4
    variation = 0.6583 * sin(torad(2 * (lP - lambda_sun)))
    lPP = lP + variation

    NP = MN - 0.16 * sin(torad(M))
    y = sin(torad(lPP - NP))
    x = cos(torad(lPP - NP))

    beta = todeg(asin(y * sin(torad(c.moon_inclination))))
    lam = fixangle(
        todeg(atan2(y * cos(torad(c.moon_inclination)), x)) + NP)

    dec = todeg(asin(
        dsin(beta) * dcos(OBLIQUITY)
        + dcos(beta) * dsin(OBLIQUITY) * dsin(lam)))
    ra = fixangle(todeg(atan2(
        dcos(beta) * dsin(lam) * dcos(OBLIQUITY)
        - dsin(beta) * dsin(OBLIQUITY),
        dcos(beta) * dcos(lam))))

    return {'ra': ra, 'dec': dec}


# Refraction (~0.567°) + semi-diameter (~0.266°) - horizontal parallax (~0.95°)
MOON_RISE_SET_ALTITUDE = 0.125


def moon_times(dt, lat, lon):
    """Calculate moonrise and moonset (UTC) for a given date and location.

    Uses the same hour-angle approach as sun_times(), but iterates because
    the Moon moves ~13°/day and its position shifts noticeably between the
    initial estimate and the actual rise/set time.

    Args:
        dt: date or datetime for which to calculate
        lat: latitude in degrees (north positive)
        lon: longitude in degrees (east positive)

    Returns:
        dict with 'moonrise' and 'moonset' as datetime objects in UTC,
        or None values if the moon doesn't rise or set on the given date.
    """
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt

    midnight = datetime(d.year, d.month, d.day)
    noon = midnight + timedelta(hours=12)

    pos = moon_position(noon)
    jd = julian_day_precise(noon)
    gmst = greenwich_mean_sidereal_time(jd)
    lst = fixangle(gmst + lon)
    ha = lst - pos['ra']
    if ha > 180:
        ha -= 360
    elif ha < -180:
        ha += 360

    transit_hours = 12.0 - ha / 15.0

    cos_omega = ((dsin(MOON_RISE_SET_ALTITUDE) - dsin(lat) * dsin(pos['dec']))
                 / (dcos(lat) * dcos(pos['dec'])))

    if abs(cos_omega) > 1.0:
        return {'moonrise': None, 'moonset': None}

    omega_hours = todeg(acos(cos_omega)) / 15.0
    rise_hours = transit_hours - omega_hours
    set_hours = transit_hours + omega_hours

    rise_hours = _refine_moon_event(midnight, rise_hours, lat, lon, rising=True)
    set_hours = _refine_moon_event(midnight, set_hours, lat, lon, rising=False)

    moonrise = None
    if rise_hours is not None and 0 <= rise_hours < 24:
        moonrise = midnight + timedelta(hours=rise_hours)

    moonset = None
    if set_hours is not None and 0 <= set_hours < 24:
        moonset = midnight + timedelta(hours=set_hours)

    return {'moonrise': moonrise, 'moonset': moonset}


def _refine_moon_event(midnight, hours_estimate, lat, lon, rising):
    """Iteratively refine a moonrise or moonset time estimate."""
    h = hours_estimate
    for _ in range(4):
        t = midnight + timedelta(hours=h)
        pos = moon_position(t)
        jd = julian_day_precise(t)
        gmst = greenwich_mean_sidereal_time(jd)
        lst = fixangle(gmst + lon)
        ha = lst - pos['ra']
        if ha > 180:
            ha -= 360
        elif ha < -180:
            ha += 360

        transit = h - ha / 15.0

        cos_o = ((dsin(MOON_RISE_SET_ALTITUDE) - dsin(lat) * dsin(pos['dec']))
                 / (dcos(lat) * dcos(pos['dec'])))
        if abs(cos_o) > 1.0:
            return None

        omega = todeg(acos(cos_o)) / 15.0
        h = transit - omega if rising else transit + omega

    return h
