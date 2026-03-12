import datetime

import pytz

from commands.command import Command
from lib import geocoding, time_util


class TimeCommand(Command):
    helpstr = "Käyttö: !aika [paikka]"

    def handle(self, message):
        location_str = message.params.strip() if message.params else None
        loc = geocoding.resolve_location(location_str, message.sender)
        if loc is None:
            message.reply_to(f"Sijaintia {location_str} ei löydy")
            return

        now_utc = datetime.datetime.now(tz=pytz.utc)
        timezone = time_util.resolve_location_timezone(
            loc.latitude,
            loc.longitude,
            reference_utc=now_utc,
        )
        local_time = now_utc.astimezone(timezone)

        if loc.source == "geocode":
            location_name = loc.resolved_name
        elif loc.source == "user_home":
            location_name = "kotisijainnissasi"
        else:
            location_name = "oletussijainnissa"

        tz_abbr = local_time.tzname() or timezone.zone
        message.reply_to(
            f"Aika paikassa {location_name}: "
            f"{local_time.strftime('%d.%m.%Y %H:%M')} ({tz_abbr})"
        )
