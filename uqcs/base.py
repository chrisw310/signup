from sqlalchemy import orm
import queue
from functools import wraps

mailer_queue = queue.Queue()
mailchimp_queue = queue.Queue()

Session = orm.sessionmaker(autocommit=True, expire_on_commit=False)


def needs_db(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        s = Session()
        with s.begin():
            result = fn(s, *args, **kwargs)
        return result
    return decorated
