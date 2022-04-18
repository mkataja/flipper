from commands.command import Command
from lib.irc_colors import Color, color


class ColorsCommand(Command):
    def handle(self, message):
        colors = [color(c.name, c) for c in Color]
        message.reply_to(", ".join(colors))
