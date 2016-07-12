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

"""
This data model supports a simplified scenario where no pharmacist intermediary
is considered, nor the use of (re)fills.  The workflow / authorization policy
is as follows:

    - A physician can write a new prescription for a patient.

    - A patient can request a prescription renewal.

    - A physician can list pending prescription renewal requests
    - A physician can approve or deny prescription renewal requests
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
    title = Column(String(100), nullable=False)
    fill_qty = Column(Integer)
    num_fills = Column(Integer)
    created_dt = Column(DateTime, default=func.now())

    medicine = relationship('Medicine')
    physician = relationship('User', foreign_keys=[physician_id])
    patient = relationship('User', foreign_keys=[patient_id])


# pending, approved, denied
class Status(Base):
    __tablename__ = 'status'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)


class RxRenewalRequest(Base):
    __tablename__ = 'rx_request'
    id = Column(Integer, primary_key=True)
    rx_id = Column(Integer, ForeignKey('prescription.id'))
    requestor_id = Column(Integer, ForeignKey('user.id'))
    status_id = Column(Integer, ForeignKey('status.id'))
    created_dt = Column(DateTime, default=func.now())

    status = relationship('Status')
    rx = relationship('Prescription', backref='renewal_request')
    requestor = relationship('User', backref='renewal_request')


def get_pending_renewals(session, physician_username):
    return session.query(RxRenewalRequest).\
        filter(RxRenewalRequest.requestor.username == physician_username).all()
