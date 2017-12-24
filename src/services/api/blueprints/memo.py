import flask
from flask.blueprints import Blueprint
from werkzeug.exceptions import abort

from models.memo import Memo
from services import database


def build_blueprint(bot_callback):
    bp = Blueprint('memo', __name__)

    @bp.route('/memo', methods=['GET'])
    def get_all():
        with database.get_session() as session:
            memos = session.query(Memo)
            return flask.jsonify(memos=[m.basic_info() for m in memos])

    @bp.route('/memo/<string:memo_name>', methods=['GET'])
    def get(memo_name):
        with database.get_session() as session:
            memo = session.query(Memo).filter_by(name=memo_name).first()
            if memo is None:
                abort(404)
            return flask.jsonify(memo=memo.full_info())

    return bp
