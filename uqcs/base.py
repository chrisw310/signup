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
        s.begin()
        try:
            result = fn(s, *args, **kwargs)
        except Exception:
            s.rollbacK()
            raise
        else:
            s.commit()
        return result
    return decorated
