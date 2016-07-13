import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from pyramid.threadlocal import get_current_request
from pyramid_yosai import YosaiForm

from .models import get_prescriptions


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
