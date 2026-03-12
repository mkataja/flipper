from datetime import datetime

import pytz

from commands.command import Command
from lib import geocoding, sun, time_util


class SunCommand(Command):
    helpstr = "Käyttö: !aurinko [yyyy-mm-dd] [paikka]"

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

        timezone = time_util.resolve_location_timezone(
            loc.latitude,
            loc.longitude,
            reference_utc=date.replace(tzinfo=pytz.utc),
        )
        message.reply_to(
            sun.format_sun_times_sentence(
                date, loc.latitude, loc.longitude, timezone)
        )
