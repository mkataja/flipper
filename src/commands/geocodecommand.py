from commands.command import Command
from lib import geocoding


class GeocodeCommand(Command):
    helpstr = "Käyttö: anna osoite parametrina"

    def handle(self, message):
        if not message.params:
            self.replytoinvalidparams(message)
            return

        address = message.params
        coordinates = geocoding.geocode(address)
        if coordinates is None:
            message.reply_to(f"Sijaintia {address} ei ole olemassa")
            return
        latdd = coordinates.latitude
        longdd = coordinates.longitude
        resolved_name = coordinates.resolved_name

        message.reply_to(
            f"{resolved_name}: {geocoding.lat_to_human(latdd)}; "
            f"{geocoding.long_to_human(longdd)} ({latdd},{longdd})"
        )
