from flask import Blueprint, request, session, redirect, abort, url_for, make_response, Response, flash, get_flashed_messages
from werkzeug import exceptions
from .templates import lookup
from .base import needs_db, mailchimp_queue, mailer_queue
import sqlalchemy.exc as sa_exc
import functools
from . import models as m
import os
import logging

# Type Imports
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Session

admin = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def clear_token(response):
    response.set_cookie('token', value='', max_age=0)
    return response


def get_user_from_token(s: Session, token: str) -> Optional[m.AdminUser]:
    qry = s.query(
        m.Session,
        m.AdminUser
    ).filter(
        m.Session.username == m.AdminUser._username,
        m.Session.token == token
    )
    sessions_users = qry.all()

    if len(sessions_users) <= 0:
        final_user = None
    elif len(sessions_users) == 1:
        user_session, user = sessions_users[0]
        if user_session.valid():
            user_session.update_expiry()
            final_user = user
        else:
            s.delete(user_session)
            final_user = None
    else:
        final_user = None
        for user_session, user in sessions_users:
            if user_session.valid():
                user_session.update_expiry()
                final_user = user
            else:
                s.delete(user_session)
    return final_user


def needs_db_and_admin(fn):
    @functools.wraps(fn)
    @needs_db
    def inner(s: Session, *args, **kwargs):
        if 'token' not in request.cookies:
            logger.debug("Forbidden: no token requesting {}".format(fn.__name__))
            return redirect('/admin/login', code=303)
        token = request.cookies.get('token')
        user = get_user_from_token(s, token)
        if user is None:
            logger.debug("Forbidden: invalid token")
            resp = redirect('/admin/login', code=303)
            clear_token(resp)
            return resp
        logger.debug("Action as {}".format(user.username))
        return fn(s, user, *args, **kwargs)
    return inner


@admin.route('/login', methods=["GET", "POST"])
@needs_db
def admin_login(s):
    if "token" in request.cookies:
        token = request.cookies.get('token')
        user = get_user_from_token(s, token)
        if user is not None:
            logger.debug('Redirecting logged in user {}'.format(user.username))
            return redirect('/admin/accept', 303)
    if request.method == "GET":
        return lookup.get_template('admin.mako').render(get_msgs=get_flashed_messages)
    if "username" in request.form:
        user = s.query(m.AdminUser).filter(
            m.AdminUser._username == request.form.get('username')
        ).first() # type: Optional[m.AdminUser]

        if user is None:
            resp = make_response(exceptions.Forbidden().get_response(request.environ))  # type: Response
            clear_token(resp)
            return resp

        password = request.form.get('password')
        if user.check_password(password.encode('utf-8')):
            user_session = m.Session(username=user.username)
            s.add(user_session)
            s.flush()
            resp = redirect('/admin/accept', 303)
            resp.set_cookie('token', user_session.token, 3600)
            logger.debug('Logging in {} with {}'.format(user.username, user_session.token))
            return resp
        else:
            flash('Username or password invalid')
            logging.info('Failed attempt to log in user {}'.format(user.username))
            return redirect('/admin/login', 303)



@admin.route('/accept')
@needs_db_and_admin
def admin_accept(s, user):
    q = s.query(m.Member).filter(m.Member.paid == None)
    return lookup.get_template('accept.mako').render(members=q)


@admin.route('/list')
@needs_db_and_admin
def admin_list(s, admin_user):
    q = s.query(m.Member)
    q2 = s.query(m.Member).filter(m.Member.paid != None)
    return lookup.get_template('list.mako').render(members=q, paid = q2)


@admin.route('/paid/<int:member_id>')
@needs_db_and_admin
def paid(s, user_id):
    if session.get('admin', 'false') == 'true':
        user = s.query(m.Member).filter(m.Member.id == user_id).one()
        user.paid = "CASH"
        mailchimp_queue.put(user)
        mailer_queue.put(user)
        return redirect("/admin/accept", 303)
    else:
        abort(403)


@admin.route('/delete/<int:member_id>')
@needs_db_and_admin
def delete(s, admin_user, member_id):
    user = s.query(m.Member).filter(m.Member.id == member_id).one()
    s.delete(user)
    return redirect("/admin/accept", 303)

@admin.route('/logout')
@needs_db_and_admin
def logout(s, admin_user):
    resp = redirect(url_for('admin.admin_login'), 303)
    clear_token(resp)
    return resp
