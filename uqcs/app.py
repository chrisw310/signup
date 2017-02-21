import os
import re
import stripe
from .templates import lookup
from flask import Flask, request, session, flash, get_flashed_messages, redirect
from . import models as m
from .admin import admin
from .base import needs_db
from .base import mailchimp_queue, mailer_queue


app = Flask(__name__)
app.register_blueprint(admin, url_prefix='/admin')

stripe.api_key = os.environ.get("STRIPE_API_KEY")


def student_checksum(first_7, last_1):
    u = [int(d) for d in first_7]
    return int(last_1) == (9*u[0] + 7*u[1]   + 3*u[2] + 9*u[3] + 7*u[4] + 3*u[5] + 9*u[6]) % 10


def user_from_request(req):
    info = {}
    if not req.form.get("fname", "").strip():
        return (None, "No first name given")
    else:
        info["first_name"] = req.form["fname"].strip()

    if not req.form.get("lname", "").strip():
        return (None, "No last name given")
    else:
        info["last_name"] = req.form["lname"].strip()

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



@app.route("/", methods=["GET", "POST"])
@needs_db
def form(s):
    stripe_pubkey = os.environ.get('STRIPE_PUBLIC_KEY')
    if request.method == "GET":
        template = lookup.get_template('form.mako')
        return template.render(request=request, get_msgs=get_flashed_messages, STRIPE_PUBLIC_KEY=stripe_pubkey), 200
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
                mailer_queue.put(user)
                mailchimp_queue.put(user)
                return redirect('/complete', 303)
            except stripe.error.CardError as e:
                flash(e.message, "danger")
                return redirect('/payment', 303)
        else:
            mailchimp_queue.put(user)
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
