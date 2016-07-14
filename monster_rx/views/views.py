from ..forms import RxRequestForm
from pyramid_yosai import LoginForm
from pyramid.view import view_config

from pyramid.httpexceptions import HTTPFound

from yosai.core import (
    AuthenticationException,
    UsernamePasswordToken,
    Yosai,
)

from ..models import (
    add_rx_request,
    get_pending_patient_requests,
    get_pending_physician_requests,
)

from pyramid.response import Response


@view_config(route_name='home')
def home(request):
    next_url = request.route_url('launchpad')
    return HTTPFound(location=next_url)


@view_config(route_name='login', renderer='../templates/login.jinja2')
def login(request):

    login_form = LoginForm(request.POST, context={'request': request})

    if request.method == "POST" and login_form.validate():

        authc_token = UsernamePasswordToken(username=login_form.username.data,
                                            password=login_form.password.data)

        try:
            subject = Yosai.get_current_subject()
            subject.login(authc_token)

            next_url = request.route_url('launchpad')
            return HTTPFound(location=next_url)

        except AuthenticationException:
            request.session.flash('Invalid Login Credentials.')
            return {'form': login_form}

    else:
        return {'form': login_form}


# requires_user
@view_config(route_name='launchpad', renderer='../templates/launchpad.jinja2')
def launchpad(request):
    # subject = Yosai.get_current_subject()
    # check_roles = subject.has_roles(['doctor', 'patient'])

    # check_roles looks like:  [('role_name', Boolean), ...]
    # roles = [role for role, check in filter(lambda x: x[1], check_roles)]

    roles = ['physician', 'patient']

    return {'roles': roles}


@view_config(route_name='request_rx', renderer='../templates/request_rx.jinja2')
def request_rx(request):

    rx_request_form = RxRequestForm(request.POST)

    if request.method == "POST" and rx_request_form.validate():
        add_rx_request(request.dbsession, rx_request_form.data['prescription'])

        # request.session.flash('RX Request Submitted.')
        next_url = request.route_url('request_rx')
        return HTTPFound(next_url)
    else:
        # current_username = Yosai.get_current_subject().primary_identifier
        current_username = 'bubzy' # temporary
        results = get_pending_patient_requests(request.dbsession, current_username).all()

        return {'rx_request_form': rx_request_form,
                'results': results,
                'user': current_username}


@view_config(route_name='rx_portal', renderer='../templates/pending_rx.jinja2')
def rx_portal(request):
    if request.method == "POST":
        print(request.POST)

    else:
        # current_username = Yosai.get_current_subject().primary_identifier
        current_username = 'drmoozy' # temporary
        results = get_pending_physician_requests(request.dbsession, current_username).all()

        return {'results': results}

# @view_config(route_name='create_rx', renderer='../templates/create_rx.jinja2')
# def create_rx(request):

#    create_rx_form = CreateRXForm(request.POST, context={'request': request})

#    if request.method == "POST" and login_form.validate():

#        create_rx_form.field.data

#        prescription = Prescription(...)

#        request.dbsession.add(prescription)

        # When a prescription gets created, a new resource-level permission could be
        # created in the yosai database, allowing resource-level authorization
        # for that new rx. However, time has not yet allowed support for adding new
        # resource to the yosai db.  Adding this to TO-DO.
        #resource = ResourceModel(name=prescription.id)
        # yosai_session



#    rx_refill_form = RxRefillForm(request.POST, context={'request': request})
    # requires an rx_id to refill
    # get patient's prescriptions from db
    # if request method = POST, the patient has submitted a form request that
    # contains the prescription that the refill request will be submitted for
    # otherwise, display a prescription refill request form
