from .app import app
from .workers import all_the_workers
from .base import work_queue, Session
from . import models as m
import sqlalchemy as sa
import os
import threading
import waitress
import logging

def main(args):
    logging.basicConfig(level=logging.DEBUG)
    engine = sa.create_engine(args[1])
    Session.configure(bind=engine)
    m.Base.metadata.create_all(engine)

    t = threading.Thread(target=all_the_workers, args=(work_queue,))
    t.start()

    app.secret_key = os.environ.get("APP_SECRET_KEY")
    waitress.serve(app, host=args[2], port=9090)
    t.join()
