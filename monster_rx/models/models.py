from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    func,
    ForeignKey,
    update,
)

from sqlalchemy.orm import (
    aliased,
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
    - A [nurse_practitioner] can [write] a new [prescription] for a [particular medicine]
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
    physician_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    medicine_id = Column(Integer, ForeignKey('medicine.id'), nullable=False)
    title = Column(String(100), nullable=False)
    fill_qty = Column(Integer, nullable=False)
    num_fills = Column(Integer, nullable=False)
    created_dt = Column(DateTime, default=func.now())

    medicine = relationship('Medicine', foreign_keys=[medicine_id])
    physician = relationship('User', foreign_keys=[physician_id])
    patient = relationship('User', backref='prescriptions', foreign_keys=[patient_id])


class RxRenewalRequest(Base):
    __tablename__ = 'rx_request'
    id = Column(Integer, primary_key=True)
    rx_id = Column(Integer, ForeignKey('prescription.id'))
    status = Column(Enum('requested', 'approved', 'denied', name='request_status'), default='requested')
    created_dt = Column(DateTime, default=func.now())

    rx = relationship('Prescription',
                      backref='renewal_requests',
                      foreign_keys=[rx_id])

def add_rx_request(session, prescription):
    return session.add(RxRenewalRequest(rx=prescription))

def get_prescriptions(session, username):
    return session.query(Prescription).join(Prescription.patient).\
        filter(User.username == username)

def get_pending_patient_requests(session, patient):
    return session.query(Prescription.title, RxRenewalRequest.created_dt).\
        join(RxRenewalRequest.rx, Prescription.patient).\
        filter(User.username == patient, RxRenewalRequest.status == 'requested')

def get_pending_physician_requests(session, physician):

    user_aliased = aliased(User)

    return session.query(RxRenewalRequest.id,
                         user_aliased.fullname.label('patient'),
                         Prescription.title.label('prescription'),
                         RxRenewalRequest.created_dt).\
        filter(RxRenewalRequest.rx_id == Prescription.id,
               Prescription.physician_id == User.id,
               Prescription.patient_id == user_aliased.id,
               User.username == physician,
               RxRenewalRequest.status == 'requested')

def approve_rx_requests(session, rx_requests):
    session.query(RxRenewalRequest).\
        filter(RxRenewalRequest.id.in_(rx_requests)).\
        update({'status': 'approved'}, synchronize_session='fetch')


def create_rx(session, physician, medicine, patient, title, fill_qty, num_fills):
    physician = session.query(User).filter(User.username == physician).first()
    new_rx = Prescription(medicine=medicine,
                          physician=physician,
                          patient=patient,
                          title=title,
                          fill_qty=fill_qty,
                          num_fills=num_fills)
    session.add(new_rx)
