"""
Shared astronomical constants and helper functions.

Based on algorithms from "Practical Astronomy With Your Calculator"
by Peter Duffett-Smith, Second Edition, as used in John Walker's
moontool.c ("A Moon for the Sun").
"""

from math import sin, cos, floor, sqrt, pi, tan, atan, modf


class AstronomicalConstants:
    # JDN stands for Julian Day Number
    # Angles here are in degrees

    # 1980 January 0.0 in JDN
    # XXX: DateTime(1980).jdn yields 2444239.5 -- which one is right?
    epoch = 2444238.5

    # Ecliptic longitude of the Sun at epoch 1980.0
    ecliptic_longitude_epoch = 278.833540

    # Ecliptic longitude of the Sun at perigee
    ecliptic_longitude_perigee = 282.596403

    # Eccentricity of Earth's orbit
    eccentricity = 0.016718

    # Semi-major axis of Earth's orbit, in kilometers
    sun_smaxis = 1.49585e8

    # Sun's angular size, in degrees, at semi-major axis distance
    sun_angular_size_smaxis = 0.533128

    # Elements of the Moon's orbit, epoch 1980.0

    # Moon's mean longitude at the epoch
    moon_mean_longitude_epoch = 64.975464
    # Mean longitude of the perigee at the epoch
    moon_mean_perigee_epoch = 349.383063

    # Mean longitude of the node at the epoch
    node_mean_longitude_epoch = 151.950429

    # Inclination of the Moon's orbit
    moon_inclination = 5.145396

    # Eccentricity of the Moon's orbit
    moon_eccentricity = 0.054900

    # Moon's angular size at distance a from Earth
    moon_angular_size = 0.5181

    # Semi-major axis of the Moon's orbit, in kilometers
    moon_smaxis = 384401.0
    # Parallax at a distance a from Earth
    moon_parallax = 0.9507

    # Synodic month (new Moon to new Moon), in days
    synodic_month = 29.53058868

    # Base date for E. W. Brown's numbered series of lunations (1923 January 16)
    lunations_base = 2423436.0

    # Properties of the Earth
    earth_radius = 6378.16


c = AstronomicalConstants()


def fixangle(angle):
    """Normalize angle to 0-360 degrees."""
    return angle - 360.0 * floor(angle / 360.0)


def torad(degrees):
    return degrees * pi / 180.0


def todeg(radians):
    return radians * 180.0 / pi


def dsin(degrees):
    return sin(torad(degrees))


def dcos(degrees):
    return cos(torad(degrees))


def kepler(m, ecc):
    """Solve the equation of Kepler."""
    epsilon = 1e-6
    m = torad(m)
    e = m
    while 1:
        delta = e - ecc * sin(e) - m
        e = e - delta / (1.0 - ecc * cos(e))
        if abs(delta) <= epsilon:
            break
    return e


def julian_day(dt):
    """Convert a date to Julian Day Number.

    Uses only the year/month/day components; time of day is ignored.
    Returns JD at noon UT of the given date.
    """
    year = int(dt.year)
    month = int(dt.month)
    day = int(dt.day)

    a = modf((month - 14) / 12.0)[1]
    jd = modf((1461 * (year + 4800 + a)) / 4.0)[1]
    jd += modf((367 * (month - 2 - 12 * a)) / 12.0)[1]
    x = modf((year + 4900 + a) / 100.0)[1]
    jd -= modf((3 * x) / 4.0)[1]
    jd += day - 2432075.5  # was 32075; add 2400000.5

    return 2400000.5 + jd


def sun_ecliptic_longitude(jd):
    """Calculate the Sun's ecliptic longitude for a given Julian Day.

    Returns a dict with:
        lambda_sun: ecliptic longitude (degrees)
        M: mean anomaly (degrees)
        sun_dist: distance to Sun (km)
        sun_angular_diameter: angular diameter (degrees)
    """
    day = jd - c.epoch

    N = fixangle((360 / 365.2422) * day)
    M = fixangle(N + c.ecliptic_longitude_epoch - c.ecliptic_longitude_perigee)

    Ec = kepler(M, c.eccentricity)
    Ec = sqrt((1 + c.eccentricity) / (1 - c.eccentricity)) * tan(Ec / 2.0)
    Ec = 2 * todeg(atan(Ec))

    lambda_sun = fixangle(Ec + c.ecliptic_longitude_perigee)
    F = ((1 + c.eccentricity * cos(torad(Ec))) / (1 - c.eccentricity ** 2))
    sun_dist = c.sun_smaxis / F
    sun_angular_diameter = F * c.sun_angular_size_smaxis

    return {
        'lambda_sun': lambda_sun,
        'M': M,
        'sun_dist': sun_dist,
        'sun_angular_diameter': sun_angular_diameter,
    }
