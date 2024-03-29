from datetime import timezone
import datetime
import logging

from sqlalchemy.sql.functions import func

import lib.time_util
from models.reminder import Reminder
from modules.module import Module
from services import database


class ReminderModule(Module):
    def __init__(self, bot):
        super().__init__(bot)
        self.next_reminder = None

    def on_welcome(self, _connection, _event):
        self._update_next()

    def refresh_reminders(self):
        self._update_next()

    def _update_next(self):
        with database.get_session() as session:
            next_reminder = session.query(func.min(Reminder.due)).one()[0]
        if next_reminder is None:
            return
        else:
            next_reminder = lib.time_util.get_utc_datetime(next_reminder)
            if next_reminder < datetime.datetime.now(timezone.utc):
                logging.warning("Missed reminders!")
        if self.next_reminder is None or next_reminder < self.next_reminder:
            self.next_reminder = next_reminder
            logging.info("Setting next reminder at {}".format(self.next_reminder))
            self._bot.reactor.scheduler.execute_at(self.next_reminder, self._process_reminders)

    def _process_reminders(self):
        self.next_reminder = None
        with database.get_session() as session:
            outstanding = (session
                           .query(Reminder)
                           .filter(Reminder.due < datetime.datetime.now()))
            for reminder in outstanding:
                success = self._try_remind(reminder)
                if not success:
                    return
                if reminder.repeat_count is not None:
                    reminder.repeat_count = reminder.repeat_count - 1
                if reminder.repeats_left():
                    reminder.due = reminder.get_next_repeat()
                else:
                    session.delete(reminder)
            session.commit()
        self._update_next()

    def _try_remind(self, reminder):
        try:
            channel = reminder.channel
            if channel:
                target = channel.name
            else:
                target = reminder.user.nick
            message = "{}: {}".format(reminder.user.nick, reminder.message)
            self._bot.privmsg(target, message)
            return True
        except Exception:
            # This may not fail
            logging.exception("Error while reminding {}".format(reminder.id))
            return False
