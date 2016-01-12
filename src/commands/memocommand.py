from commands.command import Command
from models.memo import Memo
from models.memo_line import MemoLine
from services import database, http_api


class MemoCommand(Command):
    helpstr = "Käyttö: !memo <nimi>, !memo <nimi> <viesti> tai !memo new <nimi>"

    def handle(self, message):
        parameters = message.params.split(maxsplit=1)

        if not (1 <= len(parameters) <= 2):
            self.replytoinvalidparams(message)
            return

        if len(parameters) == 1:
            self._get_memo(message, parameters)
        elif parameters[0].lower() == 'new':
            self._new_memo(message, parameters)
        else:
            self._add_line(message, parameters)

    def _get_memo(self, message, parameters):
        memo_name = parameters[0].lower()
        with database.get_session() as session:
            memo = session.query(Memo).filter_by(name=memo_name).first()
            if memo is None:
                message.reply_to("Memoa '{}' ei löydy".format(memo_name))
                return
            message.reply_to("{}".format(http_api.url_for('memo', name=memo_name)))

    def _new_memo(self, message, parameters):
        memo_name = parameters[1].lower()
        if memo_name == 'new':
            message.reply_to("Nimeä 'new' ei voi käyttää")
            return
        memo = Memo()
        memo.name = memo_name
        with database.get_session() as session:
            session.add(memo)
            session.commit()
            message.reply_to("Memo '{}' luotu".format(memo_name))

    def _add_line(self, message, parameters):
        memo_name = parameters[0].lower()
        with database.get_session() as session:
            memo = session.query(Memo).filter_by(name=memo_name).first()
            if memo is None:
                message.reply_to("Memoa '{}' ei löydy".format(memo_name))
                return
            memo_line = MemoLine()
            memo_line.memo = memo
            memo_line.content = parameters[1]
            session.add(memo_line)
            session.commit()
            message.reply_to("Lisätty ({})"
                             .format(http_api.url_for('memo', name=memo_name)))
