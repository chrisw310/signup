from sqlalchemy import orm
import queue
from functools import wraps

work_queue = queue.Queue()
Session = orm.sessionmaker(autocommit=True)


def needs_db(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        s = Session()
        with s.begin():
            result = fn(s, *args, **kwargs)
        return result
    return decorated
