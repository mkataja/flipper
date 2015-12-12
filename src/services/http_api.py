from functools import wraps
import logging
import threading

from flask import Flask
import flask
from flask.globals import request, g
from werkzeug.exceptions import abort

import config
from models.api_account import ApiAccount
from services import database


API_APPLICATION_NAME = 'flipper API'
API_VERSION = '1.0.0'

app = Flask(__name__)
_bot_callback = None

def listen(bot_callback):
    global _bot_callback  # TODO: Better implementation
    _bot_callback = bot_callback

    args = {
            'host': config.API_HOST,
            'port': config.API_PORT,
            'debug': False,
            'use_reloader': False,
            }
    logging.info("Starting HTTP API in {}:{}".format(args['host'], args['port']))
    threading.Thread(target=app.run, kwargs=args).start()


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.values.get('key'):
            key = request.values.get('key').lower()
            with database.get_session() as session:
                account = (session.query(ApiAccount)
                           .filter_by(key=key, enabled=True).first())
                if account != None:
                    logging.info("API account '{}' authenticated"
                                 .format(account.name))
                    g.account = account
                    return view_function(*args, **kwargs)
                else:
                    logging.info("Authentication failed for API key {}"
                                 .format(key))
        else:
            logging.info("API key not supplied")
        abort(401)
    return decorated_function


@app.route('/')
def root():
    return ''

@app.route('/version')
def version():
    return flask.jsonify(
                         application=API_APPLICATION_NAME,
                         api_version=API_VERSION,
                         )

# TODO wrap success/failure responses somehow
@app.route('/say', methods=['POST'])
@require_appkey
def say():
    account_name = "\x0314,1[{}]\x03".format(g.account.name)
    target = request.values.get('target')
    message = "{} {}".format(request.values.get('message'), account_name)
    _bot_callback.safe_privmsg(target, message)
    return flask.jsonify(response='ok')
