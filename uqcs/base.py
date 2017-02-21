from sqlalchemy import orm
import queue
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

mailer_queue = queue.Queue()
mailchimp_queue = queue.Queue()

DB = SQLAlchemy()
Session = DB.session


def needs_db(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        s = Session()
        with s.begin_nested():
            result = fn(s, *args, **kwargs)
        s.commit()
        return result
    return decorated
