import random

from commands.command import Command


class RealWeatherCommand(Command):
    def handle(self, message):
        weathers = ["Aurinko paistaa ja kaikilla on kivaa :)))",
                    "Lunta sataa ja kaikkia vituttaa.",
                    "Sää jatkuu sateisena koko maassa."]
        message.reply_to(random.choice(weathers))
