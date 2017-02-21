from mailchimp3 import MailChimp
import datetime as dt
import premailer
import requests
import requests.exceptions
import os
import threading
import logging
import hashlib
import functools
from queue import Queue
from .templates import lookup
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import models as m


logger = logging.getLogger(__name__)


def mailchimp_worker(queue: Queue):
    list_id = os.environ.get('MAILCHIMP_LIST_ID')
    client = MailChimp(os.environ.get("MAILCHIMP_USERNAME"), os.environ.get("MAILCHIMP_KEY"))

    for item in iter(queue.get, None):  # type: m.Member
        save_fn = None
        try:
            h = hashlib.md5()
            h.update(item.email.lower().encode('utf-8'))
            digest = h.hexdigest()
            client.lists.members.get(list_id, digest)
            save_fn = functools.partial(client.lists.members.update, list_id, digest)
        except requests.exceptions.HTTPError as e:
            save_fn = functools.partial(client.lists.members.create, list_id)

        data = {
            'email_address': item.email,
            'status': 'subscribed',
            'merge_fields': {
                'FNAME': item.first_name,
                'LNAME': item.last_name,
                'MTYPE': 'Generic',
                'GENDER': item.gender or '',
            }
        }
        if item.paid is not None:
            data['merge_fields']['PAID'] = item.paid.strip()
        if item.member_type == "student":
            data['merge_fields']['MTYPE'] = 'Student'
            data['merge_fields']['SNUM'] = item.student_no
            if item.domestic is not None:
                data['merge_fields']['DOMESTIC'] = 'Domestic' if item.domestic else 'International'
            if item.year:
                data['merge_fields']['YEAR'] = item.year
            data['merge_fields']['PROGRAM'] = str(item.program)
            if item.undergrad is not None:
                data['merge_fields']['UNDERGRAD'] = 'Undergrad' if item.undergrad else 'Postgrad'
        try:
            save_fn(data)
        except Exception as e:
            logger.exception(e)


def mailer_worker(mailqueue):
    for item in iter(mailqueue.get, None):
        try:
            print(item.first_name + ' ' + item.last_name)
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
            logger.exception(e)
