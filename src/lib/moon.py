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

from datetime import datetime
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

    # # Elements of the Moon's orbit, epoch 1980.0

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

    # Semi-mojor axis of the Moon's orbit, in kilometers
    moon_smaxis = 384401.0
    # Parallax at a distance a from Earth
    moon_parallax = 0.9507

    # Synodic month (new Moon to new Moon), in days
    synodic_month = 29.53058868

    # Base date for E. W. Brown's numbered series of lunations (1923 January 16)
    lunations_base = 2423436.0

    # # Properties of the Earth
    earth_radius = 6378.16

c = AstronomicalConstants()

# Little handy mathematical functions.
fixangle = lambda a: a - 360.0 * floor(a / 360.0)
torad = lambda d: d * pi / 180.0
todeg = lambda r: r * 180.0 / pi
dsin = lambda d: sin(torad(d))
dcos = lambda d: cos(torad(d))

def phase(phase_date=datetime.now()):
    """Calculate phase of moon as a fraction:

    The argument is the time for which the phase is requested,
    expressed in either a DateTime or by Julian Day Number.

    Returns a dictionary containing the terminator phase angle as a
    percentage of a full circle (i.e., 0 to 1), the illuminated
    fraction of the Moon's disc, the Moon's age in days and fraction,
    the distance of the Moon from the centre of the Earth, and the
    angular diameter subtended by the Moon as seen by an observer at
    the centre of the Earth."""

    # Calculation of the Sun's position

    # date within the epoch
    year = int(phase_date.year)
    month = int(phase_date.month)
    day = int(phase_date.day)

    a = modf((month - 14) / 12.0)[1]
    jd = modf((1461 * (year + 4800 + a)) / 4.0)[1]
    jd += modf((367 * (month - 2 - 12 * a)) / 12.0)[1]
    x = modf((year + 4900 + a) / 100.0)[1]
    jd -= modf((3 * x) / 4.0)[1]
    jd += day - 2432075.5  # was 32075; add 2400000.5
    
    day = 2400000.5 + jd - c.epoch

    # Mean anomaly of the Sun
    N = fixangle((360 / 365.2422) * day)
    # Convert from perigee coordinates to epoch 1980
    M = fixangle(N + c.ecliptic_longitude_epoch - c.ecliptic_longitude_perigee)

    # Solve Kepler's equation
    Ec = kepler(M, c.eccentricity)
    Ec = sqrt((1 + c.eccentricity) / (1 - c.eccentricity)) * tan(Ec / 2.0)
    # True anomaly
    Ec = 2 * todeg(atan(Ec))
    # Suns's geometric ecliptic longuitude
    lambda_sun = fixangle(Ec + c.ecliptic_longitude_perigee)

    # Orbital distance factor
    F = ((1 + c.eccentricity * cos(torad(Ec))) / (1 - c.eccentricity ** 2))

    # Distance to Sun in km
    sun_dist = c.sun_smaxis / F
    sun_angular_diameter = F * c.sun_angular_size_smaxis

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
    moon_dist = (c.moon_smaxis * (1 - c.moon_eccentricity ** 2))\
                / (1 + c.moon_eccentricity * cos(torad(MmP + mEc)))

    # Calculate Moon's angular diameter
    moon_diam_frac = moon_dist / c.moon_smaxis
    moon_angular_diameter = c.moon_angular_size / moon_diam_frac

    return {
        'phase': fixangle(moon_age) / 360.0,
        'illuminated': moon_phase,
        'age': c.synodic_month * fixangle(moon_age) / 360.0 ,
        'distance': moon_dist,
        'angular_diameter': moon_angular_diameter,
        'sun_distance': sun_dist,
        'sun_angular_diameter': sun_angular_diameter
    }

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
