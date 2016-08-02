import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from pyramid.threadlocal import get_current_request

# from pyramid_yosai import YosaiForm

from ..models import (
    get_prescriptions,
    User,
    Medicine,
)


def strip_filter(value):
    return value.strip() if value else None


def _get_prescriptions():
    session = get_current_request().dbsession

    # current_username = Yosai.get_current_subject().primary_identifier
    current_username = 'bubzy' # temporary
    return get_prescriptions(session, current_username).all()


class RxRequestForm(wtforms.Form):

    id = wtforms.HiddenField('id')

    prescription = QuerySelectField('Prescription',
                                    query_factory=lambda: _get_prescriptions(),
                                    get_label='title')


def _get_users():
    # a physician can write its own Rx!  serious jelly bean abuse may ensue...
    dbsession = get_current_request().dbsession

    return dbsession.query(User)


def _get_meds():
    dbsession = get_current_request().dbsession

    return dbsession.query(Medicine)


class WriteRXForm(wtforms.Form):

    patient = QuerySelectField('Patient',
                               query_factory=lambda: _get_users().all(),
                               get_label='fullname')

    medicine = QuerySelectField('Medicine',
                                query_factory=lambda: _get_meds().all(),
                                get_label='title')

    title = wtforms.StringField("Title",
                                filters=[strip_filter],
                                validators=[wtforms.validators.InputRequired(),
                                            wtforms.validators.Length(min=3)])

    fill_qty = wtforms.IntegerField("Qty",
                                    validators=[wtforms.validators.InputRequired()])

    num_fills = wtforms.IntegerField("Avail Fills",
                                     validators=[wtforms.validators.InputRequired()])
