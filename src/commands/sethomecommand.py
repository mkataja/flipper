from commands.command import Command
from lib import geocoding
from models.user import User


class SetHomeCommand(Command):
    helpstr = "Käyttö: anna uusi kotipaikka parametrina"

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
        user = User.get_or_create(message.sender)
        user.set_location(latdd, longdd)
        message.reply_to("Uusi kotisijainti asetettu")
