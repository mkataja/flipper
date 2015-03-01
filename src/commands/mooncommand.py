import bisect
from datetime import datetime

from commands.command import Command
from lib import moon


class MoonCommand(Command):
    helpstr = "Käyttö: voit antaa päivämäärän muodossa yyyy-mm-dd (oletus on tänään)"
    
    def handle(self, message):
        if not message.params:
            date = datetime.now()
        else:
            try:
                date = datetime.strptime(message.params, "%Y-%m-%d")
            except ValueError:
                self.replytoinvalidparams(message)
        
        result = moon.phase(date)
        illuminated = result['illuminated']
        phase = phase_string(result['phase'])
        message.reply_to("Kuun vaihe: {} ({:.0%})".format(
            phase, illuminated))


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
