from commands.command import Command
from models.memo import Memo
from models.memo_line import MemoLine
from models.user import User
from services import database


class MemoCommand(Command):
    reserved_words = ['new', 'list']
    helpstr = "Käyttö: !memo <nimi>, !memo <nimi> <viesti> tai !memo new <nimi>"

    def handle(self, message):
        parameters = message.params.split(maxsplit=1)

        if not (1 <= len(parameters) <= 2):
            self.replytoinvalidparams(message)
            return

        if parameters[0].lower() == 'new':
            self._new_memo(message, parameters)
        elif parameters[0].lower() == "list":
            self._list_memos(message)
        elif len(parameters) == 1:
            self._get_memo(message, parameters)
        else:
            self._add_line(message, parameters)

    def _get_memo(self, message, parameters):
        memo_name = parameters[0].lower()
        with database.get_session() as session:
            memo = session.query(Memo).filter_by(name=memo_name).first()
            if memo is None:
                message.reply_to("Memoa '{}' ei löydy".format(memo_name))
                return
            url = message.bot.http_api.url_for('memo.get', memo_name=memo_name)
            message.reply_to("{}".format(url))

    def _new_memo(self, message, parameters):
        memo_name = parameters[1].lower().strip()
        if not memo_name.isalnum() or memo_name in self.reserved_words:
            message.reply_to("Nimeä '{}' ei voi käyttää".format(memo_name))
            return
        with database.get_session() as session:
            memo = session.query(Memo).filter_by(name=memo_name).first()
            if memo is not None:
                message.reply_to("Memo '{}' on jo olemassa".format(memo_name))
                return
            memo = Memo()
            memo.created_by_user = User.get_or_create(message.sender)
            memo.name = memo_name
            session.add(memo)
            session.commit()
            message.reply_to("Memo '{}' luotu".format(memo_name))

    def _list_memos(self, message):
        with database.get_session() as session:
            memo_names = session.query(Memo.name).all()
            if len(memo_names) < 1:
                message.reply_to("Ei memoja")
                return
            message.reply_to(', '.join([r for r, in memo_names]))

    def _add_line(self, message, parameters):
        memo_name = parameters[0].lower()
        with database.get_session() as session:
            memo = session.query(Memo).filter_by(name=memo_name).first()
            if memo is None:
                message.reply_to("Memoa '{}' ei löydy".format(memo_name))
                return
            memo_line = MemoLine()
            memo_line.memo = memo
            memo_line.created_by_user = User.get_or_create(message.sender)
            memo_line.content = parameters[1]
            session.add(memo_line)
            session.commit()
            url = message.bot.http_api.url_for('memo.get', memo_name=memo_name)
            message.reply_to("Lisätty ({})".format(url))
