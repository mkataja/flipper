import datetime

import config
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
        
        if message.startswith(config.CMD_PREFIX):
            return
        
        e = LogEntry()
        e.target = event.target
        e.nick = event.source.nick
        e.timestamp = datetime.datetime.utcnow()
        e.message = message
        with database.get_session() as session:
            session.add(e)
            session.commit()
