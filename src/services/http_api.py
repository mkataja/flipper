from functools import wraps
import logging
import threading

from flask import Flask
import flask
from flask.globals import request
from werkzeug.exceptions import abort

import config


API_APPLICATION_NAME = 'flipper API'
API_VERSION = '1.0.0'

app = Flask(__name__)
_callback = None

def listen(callback):
    global _callback  # TODO: Better implementation
    _callback = callback

    args = {
            'host': config.API_HOST,
            'port': config.API_PORT,
            }
    logging.info("Starting HTTP API in {}:{}".format(args['host'], args['port']))
    threading.Thread(target=app.run, kwargs=args).start()


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if (request.args.get('key')
            and request.args.get('key').lower() == config.API_APP_KEY):
            return view_function(*args, **kwargs)
        else:
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
@app.route('/say', methods = ['POST'])
@require_appkey
def say():
    target = request.args.get('target')
    message = request.args.get('message')
    _callback.safe_privmsg(target, message)
    return flask.jsonify(response='ok')
