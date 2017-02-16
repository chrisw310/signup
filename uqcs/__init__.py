from .app import app, mailqueue_thread, Session
from . import models as m
import sqlalchemy as sa
import os
import threading

def main():

    engine = sa.create_engine("sqlite:///dev.db")
    m.Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    t = threading.Thread(target=mailqueue_thread)
    t.start()

    app.secret_key = os.environ.get("APP_SECRET_KEY")
    app.run(port=9090)
    t.join()
