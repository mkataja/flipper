import datetime

import config
from lib.markov_helper import parse_markov_sentences, insert_markov_sentences
from models.log_entry import LogEntry
from modules.module import Module
from services import database


class LoggingModule(Module):
    def on_privmsg(self, connection, event):
        self._log(connection, event)
    
    def on_pubmsg(self, connection, event):
        self._log(connection, event)
        
    def _log(self, connection, event):
        message = event.arguments[0]
        target = event.target
        nick = event.source.nick
        timestamp = datetime.datetime.utcnow()
        
        if message.startswith(config.CMD_PREFIX):
            return
        
        self._create_log_entry(target, nick, timestamp, message)
        
        markov_sentences = parse_markov_sentences(message)
        insert_markov_sentences(markov_sentences,
                                'imitate_{}'.format(nick.lower()),
                                '{}_{}'.format(target, timestamp.isoformat()))
    
    def _create_log_entry(self, target, nick, timestamp, message):
        e = LogEntry()
        e.target = target
        e.nick = nick
        e.timestamp = timestamp
        e.message = message
        with database.get_session() as session:
            session.add(e)
            session.commit()
