import random
import re
import threading
import time

from commands.command import Command


class RollCommand(Command):
    helpstr = "Käyttö: speksaa heitettävä noppa muodossa AdX (esim 2d6)"

    rolling = threading.Lock()

    def handle(self, message):
        acquired = RollCommand.rolling.acquire(False)
        if not acquired:
            message.reply_to("Yksi heitto kerrallaan")
            return

        try:
            self.roll(message)
        finally:
            RollCommand.rolling.release()

    def roll(self, message):
        matches = re.match("([1-9][0-9]*)d([1-9][0-9]*)",
                           message.params.strip())

        if matches is None:
            self.replytoinvalidparams(message)
            return

        num_dice = int(matches.group(1))
        num_faces = int(matches.group(2))

        if num_dice > 20:
            message.reply_to("Liikaa noppia")
            return

        if not 1 < num_faces <= 10000:
            message.reply_to("Nigga please, {}...".format(num_faces))
            return

        rolls = [random.randint(1, num_faces) for _ in range(num_dice)]

        if num_dice > 4:
            message.reply_to("Heitit: {}. Heittojen summa: {}"
                             .format(", ".join(map(str, rolls)),
                                     sum(rolls)))
        elif num_dice == 1:
            message.reply_to("Heitit: {}".format(rolls[0]))
        else:
            for roll in rolls:
                message.reply_to("Heitit: {}...".format(roll))
                time.sleep(2)
            message.reply_to("Heittojen summa: {}".format(sum(rolls)))
