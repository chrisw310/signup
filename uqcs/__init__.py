from .app import app, mailqueue_thread
import os
import threading

def main():
    t = threading.Thread(target=mailqueue_thread)
    t.start()

    app.secret_key = os.environ.get("APP_SECRET_KEY")
    app.run(port=9090)
    t.join()
