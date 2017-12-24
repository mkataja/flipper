import logging
import threading

from flask import Flask
import flask

import config
from services.api.blueprints import meta, memo, say
from services.api.json_encoder import CustomJSONEncoder


class HttpApi():
    _blueprints = [meta, memo, say]

    def __init__(self, bot_callback):
        self.bot_callback = bot_callback
        self.app = self._initialize_app()

    def _initialize_app(self):
        app = Flask(__name__)

        app.url_map.strict_slashes = False
        app.json_encoder = CustomJSONEncoder
        server_name = "{}:{}".format(config.API_HOSTNAME, config.API_PORT)
        app.config.update(SERVER_NAME=server_name)

        for bp in HttpApi._blueprints:
            app.register_blueprint(
                bp.build_blueprint(self.bot_callback),
                url_prefix='/api'
            )

        return app

    def listen(self):
        args = {
            'host': config.API_HOST,
            'port': config.API_PORT,
            'debug': False,
            'use_reloader': False,
        }
        logging.info("Starting HTTP API in {}:{}"
                     .format(args['host'], args['port']))
        threading.Thread(target=self.app.run,
                         kwargs=args,
                         name="HttpApi",
                         daemon=True).start()

    def url_for(self, *args, **kwargs):
        with self.app.app_context():
            return flask.url_for(*args, **kwargs)
