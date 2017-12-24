import flask
from flask.blueprints import Blueprint
from flask.globals import request, g

from lib.irc_colors import color, Color

from services.api.decorators import require_appkey


def build_blueprint(bot_callback):
    bp = Blueprint('say', __name__)

    # TODO wrap success/failure responses somehow
    # TODO check required parameters
    # TODO take parameters as JSON
    @bp.route('/say', methods=['POST'])
    @require_appkey
    def say():
        account_name = color("[{}]".format(g.account.name), Color.dgrey)
        target = request.values.get('target')
        message = "{} {}".format(request.values.get('message'), account_name)
        bot_callback.privmsg(target, message)
        return flask.jsonify(response='ok')

    return bp
