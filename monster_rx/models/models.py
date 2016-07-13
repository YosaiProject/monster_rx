from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    func,
    ForeignKey,
)

from sqlalchemy.orm import (
    relationship,
)

from .meta import Base
from sqlalchemy.types import Enum

"""
Don't waste your time questioning the real-world validity of this data model.
This data model supports a simplified scenario where no pharmacist intermediary
is considered, nor the use of (re)fills.  Further, a hypothetical constraint
is introduced so as to illustrate resource-level permissions (writing rx's, see below).

The workflow / authorization policy is as follows:

    Domain-Level Authorization:
    - A [patient] can [request] a [prescription renewal].

    - A [physician] can [view] [pending prescription renewal requests]
    - A [physician] can [approve] or [deny] [prescription renewal requests]

    Resource-Level Authorization:
    - A [physician] can [write] a new [prescription] for a [particular medicine] (let's imagine that it's a regulation, for this example)
"""

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    fullname = Column(String(255))


class Medicine(Base):
    __tablename__ = 'medicine'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))


class Prescription(Base):
    __tablename__ = 'prescription'
    id = Column(Integer, primary_key=True)
    physician_id = Column(Integer, ForeignKey('user.id'))
    patient_id = Column(Integer, ForeignKey('user.id'))
    medicine_id = Column(Integer, ForeignKey('medicine.id'))
    title = Column(String(100))
    fill_qty = Column(Integer)
    num_fills = Column(Integer)
    created_dt = Column(DateTime, default=func.now())

    medicine = relationship('Medicine', foreign_keys=[medicine_id])
    physician = relationship('User', foreign_keys=[physician_id])
    patient = relationship('User', foreign_keys=[patient_id])


class RxRenewalRequest(Base):
    __tablename__ = 'rx_request'
    id = Column(Integer, primary_key=True)
    rx_id = Column(Integer, ForeignKey('prescription.id'))
    requestor_id = Column(Integer, ForeignKey('user.id'))
    status = Column(Enum('requested', 'approved', 'denied', name='request_status'), default='requested')
    created_dt = Column(DateTime, default=func.now())

    rx = relationship('Prescription', backref='renewal_request', foreign_keys=[rx_id])
    requestor = relationship('User', backref='renewal_request', foreign_keys=[requestor_id])


def get_prescriptions(session, username):
    return session.query(Prescription).filter(Prescription.patient.username == username)


def get_pending_requests(session, physician_username):
    return session.query(RxRenewalRequest).\
        join(RxRenewalRequest.rx, Prescription.physician).\
        filter(User.username == physician_username)
