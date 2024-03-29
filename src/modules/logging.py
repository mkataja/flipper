import datetime

from lib import markov_helper
from models.imitate_corpus import ImitateCorpus
from models.log_entry import LogEntry
from modules.message_handler import MessageHandler
from services import database


class LoggingModule(MessageHandler):
    def handle(self, message):
        self._log(message)

    def _log(self, message):
        timestamp = datetime.datetime.utcnow()

        self._create_log_entry(message.channel.id, message.user.id, timestamp, message.content)
        if not message.is_private_message:
            self._create_imitate_entry(message.channel, message.user, timestamp, message.content)

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
