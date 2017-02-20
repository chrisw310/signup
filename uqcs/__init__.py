from .app import app
from .workers import mailchimp_worker, mailer_worker
from .base import mailchimp_queue, mailer_queue, Session
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

    mailchimp_thread = threading.Thread(
        target=mailchimp_worker,
        args=(mailchimp_queue,),
    )
    mailer_thread = threading.Thread(
        target=mailer_worker,
        args=(mailer_queue,),
    )
    mailchimp_thread.start()
    mailer_thread.start()

    app.secret_key = os.environ.get("APP_SECRET_KEY")
    waitress.serve(app, host=args[2], port=9090)

    mailchimp_queue.put(None)
    mailer_queue.put(None)

    mailchimp_thread.join(5000)
    mailer_thread.join(5000)
