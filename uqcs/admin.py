from flask import Blueprint, request, session, redirect, abort
from .templates import lookup
from .base import needs_db, mailchimp_queue, mailer_queue
from . import models as m
import os

admin = Blueprint('admin', __name__)


@admin.route('/login', methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        if session.get('admin', 'false') == 'true':
            return redirect('/admin/accept', 303)
        return lookup.get_template("admin.mako").render()
    else:
        if "password" in request.form and request.form["password"] == os.environ.get("ADMIN_PASSWORD"):
            session['admin'] = 'true'
            return redirect('/admin/accept', 303)


@admin.route('/accept')
@needs_db
def admin_accept(s):
    if session.get('admin', 'false') == 'true':
        q = s.query(m.Member).filter(m.Member.paid == None)
        return lookup.get_template('accept.mako').render(members=q)
    else:
        abort(403)


@admin.route('/list')
@needs_db
def admin_list(s):
    if session.get('admin', 'false') == 'true':
        q = s.query(m.Member)
        q2 = s.query(m.Member).filter(m.Member.paid != None)
        return lookup.get_template('list.mako').render(members=q, paid = q2)
    else:
        abort(403)


@admin.route('/paid/<int:user_id>')
@needs_db
def paid(s, user_id):
    if session.get('admin', 'false') == 'true':
        user = s.query(m.Member).filter(m.Member.id == user_id).one()
        user.paid = "CASH"
        mailchimp_queue.put(user)
        mailer_queue.put(user)
        return redirect("/admin/accept", 303)
    else:
        abort(403)


@admin.route('/delete/<int:user_id>')
@needs_db
def delete(s, user_id):
    if session.get('admin', 'false') == 'true':
        user = s.query(m.Member).filter(m.Member.id == user_id).one()
        s.delete(user)
        return redirect("/admin/accept", 303)
    else:
        abort(403)