import datetime
import re

from commands.command import Command
from models.channel import Channel
from models.reminder import Reminder
from models.user import User
from modules.reminder import ReminderModule


class ReminderFormatError(ValueError):
    pass


class ReminderCommand(Command):
    helpstr = ("Käyttö: 16:20[:00]: maksa laskut "
               "| +00:45: kakut uunista "
               "| [yli]huomenna[ 15:00]: osta suklaata "
               "| 19.4.[ 12:00]: muistilappu "
               "| 21:00 joka [7. ]päivä: nukkumaanmenoaika! "
               "| yhdistele edellisiä "
               "| lista "
               "| peru <ID>")

    # TODO: Repeat count
    pattern = re.compile(
        r"^(?:(?P<datestring>(?:yli)?huomenna)|"
        "(?:(?P<day>\d\d?)\.(?P<month>\d\d?)\.(?P<year>\d\d\d\d)?)|"
        "(?P<timer>\+))?\s*(?:(?P<hours>\d\d?):(?P<minutes>\d\d)(?::(?P<seconds>\d\d))?)?"
        "(?:\s+(?:joka\s+(?:(?P<repeat_n>\d+)\.?\s+)?(?P<repeat_length>päivä|tunti)))?"
        ":\s+(?P<message>.+)$"
    )

    default_time = datetime.time(9, 0, 0)

    def handle(self, message):
        parameters = message.params.split(maxsplit=1)
        if parameters[0].lower() == 'peru':
            self._delete_reminder(message, parameters)
        elif parameters[0].lower() == "lista":
            self._list_reminders(message)
        else:
            self._create_reminder(message)

    def _get_user_and_channel(self, message):
        user_id = User.get_or_create(message.sender).id
        if message.is_private_message:
            channel_id = None
        else:
            channel_id = Channel.get_or_create(message.source).id
        return user_id, channel_id

    def _delete_reminder(self, message, parameters):
        try:
            reminder_id = int(parameters[1])
        except (ValueError, IndexError):
            message.reply_to("Virheellinen ID")
            return
        user_id, channel_id = self._get_user_and_channel(message)
        success = Reminder.delete(reminder_id, user_id, channel_id)
        if success:
            message.reply_to("Ok")
        else:
            message.reply_to("Ei löytynyt")

    def _list_reminders(self, message):
        user_id, channel_id = self._get_user_and_channel(message)
        reminders = [r.short_string() for r in
                     Reminder.list_for_user(user_id, channel_id)]
        if len(reminders) == 0:
            message.reply_to("Ei muistutuksia")
        else:
            message.reply_to('; '.join(reminders))

    def _create_reminder(self, message):
        try:
            data = [g.groupdict() for g in
                    ReminderCommand.pattern.finditer(message.params.strip())][0]
        except IndexError:
            message.reply_to("Virheellinen muotoilu")
            return

        try:
            due = self._parse_when(data)
        except (ValueError, ReminderFormatError):
            message.reply_to("Virheellinen aikamuotoilu")
            return
        due = due.replace(microsecond=0)

        if due <= datetime.datetime.now():
            message.reply_to("{} meni jo!".format(due))
            return

        try:
            repeat_interval, repeat_count = self._parse_repeat(data)
        except ReminderFormatError:
            message.reply_to("Virheellinen toisto")
            return

        text = data['message']
        user_id, channel_id = self._get_user_and_channel(message)

        reminder = Reminder.create(user_id, channel_id,
                                   due, text,
                                   repeat_interval, repeat_count)
        message.bot.get_module_instance(ReminderModule).refresh_reminders()

        message.reply_to("Ok, muistutus [{}] {}".format(reminder.id, reminder.due))

    def _parse_repeat(self, data):
        if data['repeat_length'] is None:
            return (None, None)

        try:
            n = int(data['repeat_n'])
            if n < 1:
                raise(ReminderFormatError("Repeat n < 1"))
        except KeyError:
            n = 1

        try:
            hours = {'tunti': 1, 'päivä': 24}[data['repeat_length']]
            interval = datetime.timedelta(hours=n * hours)
        except KeyError:
            raise(ReminderFormatError(data['repeat_length']))

        count = None
        return (interval, count)

    def _parse_time(self, data):
        time = datetime.time(int(data['hours']),
                             int(data['minutes']),
                             int(data['seconds'] or 0))
        return time

    def _parse_date(self, data, time):
        if data['year']:
            date = datetime.date(int(data['year']),
                                 int(data['month']),
                                 int(data['day']))
        else:
            date = datetime.date(datetime.datetime.now().year,
                                 int(data['month']),
                                 int(data['day']))
            if datetime.datetime.combine(date, time) <= datetime.datetime.now():
                date = date + datetime.timedelta(years=1)
        return date

    def _parse_datestring(self, datestring):
        try:
            days = {'huomenna': 1, 'ylihuomenna': 2}[datestring]
        except KeyError:
            raise(ReminderFormatError("Invalid datestring {}".format(datestring)))
        return datetime.date.today() + datetime.timedelta(days=days)

    def _get_default_date(self, time):
        if time > datetime.datetime.now().time():
            return datetime.date.today()
        else:
            return datetime.date.today() + datetime.timedelta(days=1)

    def _parse_timer(self, data):
        delta = datetime.timedelta(hours=int(data['hours']),
                                   minutes=int(data['minutes']),
                                   seconds=int(data['seconds'] or 0))
        return datetime.datetime.now() + delta

    def _parse_when(self, data):
        if data['timer']:
            time = self._parse_timer(data)
            return time

        if data['hours']:
            time = self._parse_time(data)
        else:
            time = ReminderCommand.default_time

        if data['day']:
            date = self._parse_date(data, time)
        elif data['datestring']:
            date = self._parse_datestring(data['datestring'])
        else:
            date = self._get_default_date(time)

        return datetime.datetime.combine(date, time)
