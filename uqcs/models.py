from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import *


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
    paid = Column(String(40))

    __mapper_args__ = {
        "polymorphic_on": member_type,
        "polymorphic_identity": "generic",
    }

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
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, unique=True)
    password = Column(String(60))
    name = Column(UnicodeText)


def register_from_request(request=None):
    if request is None:
        return
    pass
