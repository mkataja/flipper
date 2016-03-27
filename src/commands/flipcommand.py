import random

from commands.command import Command


class FlipCommand(Command):
    helpstr = "Käyttö: anna vaihtoehdot (1...n) kauttaviivoilla erotettuna"

    def handle(self, message):
        flips = message.params.split("/")
        flips = [x.strip() for x in flips if x.strip() != ""]

        if not flips:
            self.replytoinvalidparams(message)
        else:
            if len(flips) == 1:
                flips = ["Jaa", "Ei"]
            message.reply_to(random.choice(flips))
