from mailchimp3 import MailChimp
import datetime as dt
import premailer
import requests
import os
import threading
from queue import Queue
from .templates import lookup
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import models as m


def all_the_workers(queue):
    mailchimp_queue = Queue()
    mailer_queue = Queue()

    mail_thread = threading.Thread(target=mailer_worker, args=(mailer_queue,))
    chimp_thread = threading.Thread(target=mailchimp_worker, args=(mailchimp_queue,))

    chimp_thread.start()
    mail_thread.start()

    for item in iter(queue.get, None):
        mailchimp_queue.put(item)
        mailer_queue.put(item)

    mailchimp_queue.put(None)
    mailer_queue.put(None)

    mail_thread.join()
    chimp_thread.join()


def mailchimp_worker(queue: Queue):
    list_id = os.environ.get('MAILCHIMP_LIST_ID')
    client = MailChimp(os.environ.get("MAILCHIMP_USERNAME"), os.environ.get("MAILCHIMP_KEY"))

    for item in iter(queue.get, None):  # type: m.Member
        data = {
            'email_address': item.email,
            'status': 'subscribed',
            'merge_fields': {
                'FNAME': item.first_name,
                'LNAME': item.last_name,
                'MTYPE': item.member_type,
                'GENDER': item.gender or '',
            }
        }
        if item.member_type == "student":
            data['merge_fields']['SNUM'] = item.student_no
            data['merge_fields']['DOMESTIC'] = str(item.domestic)
            data['merge_fields']['YEAR'] = str(item.year)
            data['merge_fields']['PROGRAM'] = str(item.program)
            data['merge_fields']['UNDERGRAD'] = str(item.undergrad)
        client.lists.members.create(list_id, data)


def mailer_worker(mailqueue):
    for item in iter(mailqueue.get, None):
        try:
            print(item.name)
            receiptText = lookup.get_template("email.mtxt") \
                .render(user=item, dt=dt)
            receiptHTML = lookup.get_template('email.mako') \
                .render(user=item, dt=dt)
            requests.post("https://api.mailgun.net/v3/uqcs.org.au/messages",
                          auth=('api', os.environ.get("MAILGUN_API_KEY")),
                          data={
                              'from': 'receipts@uqcs.org.au',
                              'to': item.email,
                              'bcc': "receipts@uqcs.org.au",
                              'text': receiptText,
                              'html': premailer.transform(receiptHTML),
                              'subject': "UQCS 2017 Membership Receipt",
                          })
        except Exception as e:
            print(e)
