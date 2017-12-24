from functools import wraps
import logging

from flask.globals import request, g
from werkzeug.exceptions import abort

from models.api_account import ApiAccount
from services import database


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.values.get('key'):
            key = request.values.get('key').lower()
            with database.get_session() as session:
                account = (session.query(ApiAccount)
                           .filter_by(key=key, enabled=True).first())
                if account is not None:
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
