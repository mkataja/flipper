import datetime

from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Text, Integer, DateTime, Interval

from models.channel import Channel
from models.user import User
from services import database


class Reminder(database.FlipperBase):
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    channel_id = Column(Integer, ForeignKey(Channel.id))
    due = Column(DateTime, nullable=False)
    repeat_interval = Column(Interval)
    repeat_count = Column(Integer)
    message = Column(Text, nullable=False)

    user = relationship(User)
    channel = relationship(Channel)

    def repeats_left(self):
        return (self.repeat_interval is not None and
                (self.repeat_count is None or self.repeat_count > 0))

    def get_next_repeat(self):
        due = self.due + self.repeat_interval
        if due < datetime.datetime.now():
            due = datetime.datetime.now()
        return due

    def short_string(self):
        message = (self.message[:12] + '...') if len(self.message) > 15 else self.message
        repeats = '(R)' if self.repeat_interval else ''
        return "[{}] {}{} {}".format(self.id, self.due, repeats, message)

    @classmethod
    def create(cls, user_id, channel_id, due, message, repeat_interval, repeat_count):
        with database.get_session() as session:
            reminder = Reminder()
            reminder.user_id = user_id
            reminder.channel_id = channel_id
            reminder.due = due
            reminder.message = message
            reminder.repeat_interval = repeat_interval
            reminder.repeat_count = repeat_count
            session.add(reminder)
            session.commit()
            return reminder

    @classmethod
    def list_for_user(cls, user_id, channel_id):
        with database.get_session() as session:
            return (session
                    .query(Reminder)
                    .filter_by(user_id=user_id, channel_id=channel_id)
                    .order_by(Reminder.due))

    @classmethod
    def delete(cls, reminder_id, user_id, channel_id):
        with database.get_session() as session:
            reminder = (session
                        .query(Reminder)
                        .filter_by(id=reminder_id, user_id=user_id, channel_id=channel_id)
                        .first())
            if reminder is None:
                return False
            else:
                session.delete(reminder)
                session.commit()
                return True
