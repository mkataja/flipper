import bisect
import logging
from datetime import datetime

import pytz

from commands.command import Command
from lib import geocoding, moon, time_util


class MoonCommand(Command):
    helpstr = "Käyttö: !kuu [yyyy-mm-dd] [paikka]"

    def handle(self, message):
        params = message.params.strip() if message.params else ""
        date = datetime.now()
        location_str = None

        if params:
            parts = params.split(None, 1)
            try:
                date = datetime.strptime(parts[0], "%Y-%m-%d")
                location_str = parts[1].strip() if len(parts) > 1 else None
            except ValueError:
                location_str = params

        loc = geocoding.resolve_location(location_str, message.sender)
        if loc is None:
            message.reply_to(f"Sijaintia {location_str} ei löydy")
            return

        lat = loc.latitude
        lon = loc.longitude
        logging.info(f"Getting moon data for ({lat}, {lon})")

        result = moon.phase(date)
        illuminated = result['illuminated']
        phase_str = phase_string(result['phase'])

        times = moon.moon_times(date, lat, lon)
        moonrise = times.get('moonrise')
        moonset = times.get('moonset')

        tz = time_util.resolve_location_timezone(
            lat,
            lon,
            reference_utc=date.replace(tzinfo=pytz.utc),
        )
        time_parts = []
        if moonrise:
            rise_local = moonrise.replace(tzinfo=pytz.utc).astimezone(tz)
            time_parts.append(f"nousee {rise_local.strftime('%H:%M')}")
        if moonset:
            set_local = moonset.replace(tzinfo=pytz.utc).astimezone(tz)
            time_parts.append(f"laskee {set_local.strftime('%H:%M')}")

        time_str = ""
        if time_parts:
            time_str = " Kuu " + " ja ".join(time_parts) + "."

        message.reply_to(
            f"Kuun vaihe: {phase_str} ({illuminated:.1%}).{time_str}"
        )


def phase_string(p):
    precision = 0.03
    new = 0 / 4.0
    first = 1 / 4.0
    full = 2 / 4.0
    last = 3 / 4.0
    nextnew = 4 / 4.0

    phase_strings = (
        (new + precision, "uusikuu"),
        (first - precision, "kasvava sirppi"),
        (first + precision, "ensimmäinen neljännes"),
        (full - precision, "kasvava kuperakuu"),
        (full + precision, "täysikuu AUUUUUUUUUU"),
        (last - precision, "vähenevä kuperakuu"),
        (last + precision, "viimeinen neljännes"),
        (nextnew - precision, "vähenevä sirppi"),
        (nextnew + precision, "uusikuu"))

    i = bisect.bisect([a[0] for a in phase_strings], p)
    return phase_strings[i][1]
