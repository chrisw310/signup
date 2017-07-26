from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import (
    Column, Integer, DateTime, Enum, String, UnicodeText, Text, Boolean, ForeignKey, func, Interval, text, DateTime
)
from sqlalchemy.ext.hybrid import hybrid_property
import tzlocal
import bcrypt
import logging
import datetime as dt
logger = logging.getLogger(__name__)


class FormError(Exception):
    pass


class Ancestor(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

Base = declarative_base(cls=Ancestor)


class Member(Base):
    id = Column(Integer, primary_key=True, unique=True, nullable=False, autoincrement=True)
    first_name = Column(UnicodeText)
    last_name = Column(UnicodeText)
    email = Column(Text)
    member_type = Column(String(20))
    gender = Column(Enum("M", "F", name="gender"), nullable=True)
    _paid = Column('paid', String(40))
    time_registered = Column(DateTime, default=dt.datetime.utcnow)
    time_paid = Column(DateTime)

    __mapper_args__ = {
        "polymorphic_on": member_type,
        "polymorphic_identity": "generic",
    }

    @hybrid_property
    def paid(self):
        return self._paid

    @paid.setter
    def paid(self, value):
        self._paid = value
        self.time_paid = dt.datetime.utcnow()

    def has_paid(self):
        return self.paid is not None


class Student(Member):
    id = Column(Integer, ForeignKey(Member.id), primary_key=True)
    student_no = Column(String(8), unique=True)
    domestic = Column(Boolean)
    year = Column(Integer)
    program = Column(String(100))
    undergrad = Column(Boolean)

    __mapper_args__ = {
        "polymorphic_identity": "student"
    }

    def from_dict(self, d):
        pass

    def from_member(self, m):
        return Student(
                name=m.name,
                email=m.email,
                gender=m.gender
            )


class AdminUser(Base):
    _username = Column('username', Text, primary_key=True)
    name = Column(Text)
    _password = Column('password', String(60), nullable=True)

    @property
    def username(self) -> str:
        return self._username.lower()

    @username.setter
    def username(self, val: str) -> None:
        self._username = val.lower()

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        else:
            return self.username

    @display_name.setter
    def display_name(self, val: str) -> None:
        self.name = val

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, val):
        self._password = bcrypt.hashpw(val, bcrypt.gensalt())

    def set_password(self, password, hashed=False):
        if hashed:
            self.password = password
        else:
            self._password = password

    def check_password(self, password):
        return bcrypt.checkpw(password, self._password.encode('utf-8'))


class Session(Base):
    EXPIRY_TIME = dt.timedelta(hours=1)
    token = Column(PGUUID, primary_key=True, server_default=text('uuid_generate_v4()'))
    username = Column(Text, ForeignKey(AdminUser._username))
    issued_datetime = Column(DateTime(), default=dt.datetime.now, server_default='now')
    logger = logger.getChild('Session')

    @declared_attr
    def expiry_datetime(self):
        return Column(DateTime(), nullable=True, default=lambda: dt.datetime.now() + self.EXPIRY_TIME)

    def valid(self):
        now = dt.datetime.now()
        if now < self.expiry_datetime:
            self.logger.debug("Session for user {} is valid at {}".format(self.username, now))
            return True
        else:
            self.logger.debug("Session for user {} has expired at {}, expiry time {}".format(self.username, now, self.expiry_datetime))
            return False

    def update_expiry(self):
        self.logger.debug('Updating token for user with username {}'.format(self.username))
        self.expiry_datetime = dt.datetime.now() + self.EXPIRY_TIME


def register_from_request(request=None):
    if request is None:
        return
    pass
