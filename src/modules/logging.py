import datetime

import config
from lib import markov_helper
from models.channel import Channel
from models.imitate_corpus import ImitateCorpus
from models.log_entry import LogEntry
from models.user import User
from modules.module import Module
from services import database


class LoggingModule(Module):
    def on_privmsg(self, connection, event):
        self._log(connection, event, is_private_message=True)

    def on_pubmsg(self, connection, event):
        self._log(connection, event, is_private_message=False)

    def _log(self, connection, event, is_private_message):
        message = event.arguments[0]
        channel = Channel.get_or_create(event.target)
        user = User.get_or_create(event.source.nick)
        timestamp = datetime.datetime.utcnow()

        if message.startswith(config.CMD_PREFIX):
            return

        self._create_log_entry(channel.id, user.id, timestamp, message)
        if not is_private_message:
            self._create_imitate_entry(channel, user, timestamp, message)

    def _create_log_entry(self, channel_id, user_id, timestamp, message):
        e = LogEntry()
        e.channel_id = channel_id
        e.user_id = user_id
        e.timestamp = timestamp
        e.message = message
        with database.get_session() as session:
            session.add(e)
            session.commit()

    def _create_imitate_entry(self, channel, user, timestamp, message):
        corpus_id = ImitateCorpus.get_or_create(channel, user)
        text_identifier = '{}_{}'.format(channel.name, timestamp.isoformat())
        markov_helper.insert_text(message, corpus_id, text_identifier)
