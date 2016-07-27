from flask import Flask, request, session, flash, get_flashed_messages, redirect, abort
import threading
import queue
import stripe
from mako.lookup import TemplateLookup
from functools import wraps
import models as m
import sqlalchemy as sa
from sqlalchemy import orm
import os
import re
import requests
import datetime as dt
import premailer

app = Flask(__name__)

stripe.api_key = os.environ.get("STRIPE_API_KEY")

# db
engine = sa.create_engine("sqlite:///dev.db")
Session = orm.sessionmaker(bind=engine, autocommit=True)

m.Base.metadata.create_all(engine)

# templates
lookup = TemplateLookup([".", "Views", "templates"])


def student_checksum(first_7, last_1):
    u = [int(d) for d in first_7]
    return int(last_1) == (9*u[0] + 7*u[1] + 3*u[2] + 9*u[3] + 7*u[4] + 3*u[5] + 9*u[6]) % 10


def user_from_request(req):
    info = {}
    if not req.form.get("name", "").strip():
        return (None, "No name given")
    else:
        info["name"] = req.form["name"].strip()

    if not req.form.get("email", "").strip():
        return (None, "No email given")
    else:
        info["email"] = req.form["email"].strip()

    if req.form.get("gender", "null") not in ["null", 'M', 'F']:
        return (None, "Invalid option for gender")
    else:
        info["gender"] = req.form.get("gender", "null")
        if info["gender"] == "null":
            info["gender"] = None

    if req.form.get("student", False):
        info['student_no'] = req.form["student-no"]
        if re.match("[1-5][0-9]{7,7}", info['student_no']) is None:
            return None, "Invalid student number format"
        elif not student_checksum(info['student_no'][:7], info['student_no'][7]):
            return None, "Student number has valid format but is not a valid number"

        if "year" in req.form:
            if req.form['year'] == "5+":
                info['year'] = 5
            else:
                try:
                    info['year'] = int(req.form['year'])
                except ValueError:
                    return None, "Invalid selection for year"
            if info['year'] not in range(1, 6):
                return None, "Invalid selection for year"
        if 'domORint' in req.form:
            if req.form['domORint'].lower() not in ['domestic', 'international']:
                return None, "Invalid domestic/international option"
            info["domestic"] = req.form['domORint'].lower() == 'domestic'
        if 'degreeType' in req.form:
            if req.form['degreeType'].lower() not in ['undergrad', 'postgrad']:
                return None, "Invalid degree type option"
            info["undergrad"] = req.form['degreeType'].lower() == 'undergrad'
        if 'degree' in req.form:
            info['program'] = req.form['degree'][:100]
        return m.Student(**info), "Success"
    else:
        return m.Member(**info), "Success"

mailqueue = queue.Queue()

def needs_db(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        s = Session()
        with s.begin():
            return fn(s, *args, **kwargs)
    return decorated


@app.route("/", methods=["GET", "POST"])
@needs_db
def form(s):
    if request.method == "GET":
        template = lookup.get_template('form1.mako')
        return template.render(request=request, get_msgs=get_flashed_messages), 200
    else:
        if s.query(m.Member).filter(m.Member.email == request.form.get('email')).count() > 0:
            flash("That email has already been registered", 'danger')
            return redirect('/', 303)
        if request.form.get('student', False):
            if s.query(m.Student).filter(
                        m.Student.student_no == request.form.get('student-no')
                    ).count() > 0:
                flash("That student number has already been registered", 'danger')
                return redirect('/', 303)
        user, msg = user_from_request(request)
        if user is None:
            flash(msg, 'danger')
            return redirect('/', 303)
        s.add(user)
        if request.form['stripeToken'].strip():
            try:
                charge = stripe.Charge.create(
                    amount=540,
                    currency="aud",
                    source=request.form['stripeToken'],
                    description="UQCS Membership"
                )
                user.paid = charge['id']
                session['email'] = user.email
                mailqueue.put(user)
                return redirect('/complete', 303)
            except stripe.error.CardError as e:
                flash(e.message, "danger")
                return redirect('/payment', 303)
        else:
            session['email'] = user.email
            return redirect('/complete', 303)


@app.route("/complete")
@needs_db
def complete(s):
    if "email" not in session:
        return redirect('/', 303)
    user = s.query(m.Member)\
        .filter(m.Member.email == session["email"])\
        .one()
    return lookup.get_template("complete.mako").render(
        member=user)


@app.route('/admin/login', methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        if session.get('admin', 'false') == 'true':
            return redirect('/admin/accept', 303)
        return lookup.get_template("admin.mako").render()
    else:
        if "password" in request.form and request.form["password"] == os.environ.get("ADMIN_PASSWORD"):
            session['admin'] = 'true'
            return redirect('/admin/accept', 303)


@app.route('/admin/accept')
@needs_db
def admin_accept(s):
    if session.get('admin', 'false') == 'true':
        q = s.query(m.Member).filter(m.Member.paid == None)
        return lookup.get_template('accept.mako').render(members=q)
    else:
        abort(403)

@app.route('/admin/list')
@needs_db
def admin_list(s):
    if session.get('admin', 'false') == 'true':
        q = s.query(m.Member)
        q2 = s.query(m.Member).filter(m.Member.paid != None)
        return lookup.get_template('list.mako').render(members=q, paid = q2)
    else:
        abort(403)


@app.route('/admin/paid/<int:user_id>')
@needs_db
def paid(s, user_id):
    if session.get('admin', 'false') == 'true':
        user = s.query(m.Member).filter(m.Member.id == user_id).one()
        user.paid = "CASH"
        mailqueue.put(user)
        return redirect("/admin/accept", 303)
    else:
        abort(403)

@app.route('/admin/delete/<int:user_id>')
@needs_db
def delete(s, user_id):
    if session.get('admin', 'false') == 'true':
        user = s.query(m.Member).filter(m.Member.id == user_id).one()
        s.delete(user)
        return redirect("/admin/accept", 303)
    else:
        abort(403)


def mailqueue_thread():
    while True:
        try:
            item = mailqueue.get()
            if isinstance(item, type(None)):
                break
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
                              'subject': "UQCS 2016 Membership Receipt",
                          })
        except Exception as e:
            print(e)

t = threading.Thread(target=mailqueue_thread)
t.start()

app.secret_key = os.environ.get("APP_SECRET_KEY")
app.run(port=9090)
t.join()
