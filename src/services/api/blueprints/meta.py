import flask
from flask.blueprints import Blueprint

from services.api.constants import API_APPLICATION_NAME, API_VERSION


def build_blueprint(bot_callback):
    bp = Blueprint('meta', __name__)

    @bp.route('/version')
    def version():
        return flask.jsonify(
            application=API_APPLICATION_NAME,
            api_version=API_VERSION,
        )

    return bp
