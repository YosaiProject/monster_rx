from ..forms import RxRequestForm, WriteRXForm
from pyramid_yosai import LoginForm
from pyramid.view import view_config

from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPUnauthorized

from yosai.core import (
    AuthenticationException,
    AuthorizationException,
    IdentifiersNotSetException,
    UsernamePasswordToken,
    load_logconfig,
)

from yosai.web import WebYosai

from ..models import (
    add_rx_request,
    approve_rx_requests,
    get_pending_patient_requests,
    get_pending_physician_requests,
    create_rx,
)

load_logconfig()

@view_config(route_name='home')
def home(request):

    subject = WebYosai.get_current_subject()

    if subject.authenticated:
        next_url = request.route_url('launchpad')
    else:
        next_url = request.route_url('login')

    return HTTPFound(location=next_url)


@view_config(route_name='login', renderer='../templates/login.jinja2')
def login(request):

    login_form = LoginForm(request.POST, context={'request': request})

    if request.method == "POST" and login_form.validate():

        authc_token = UsernamePasswordToken(username=login_form.username.data,
                                            password=login_form.password.data)

        try:
            subject = WebYosai.get_current_subject()
            subject.login(authc_token)

            next_url = request.route_url('launchpad')
            return HTTPFound(location=next_url)

        except AuthenticationException:
            # request.session.flash('Invalid Login Credentials.')
            return {'login_form': login_form}

    else:
        return {'login_form': login_form}


@view_config(route_name='launchpad', renderer='../templates/launchpad.jinja2')
@WebYosai.requires_user
def launchpad(context, request):
    subject = WebYosai.get_current_subject()

    # check_roles looks like:  [('role_name', Boolean), ...]
    check_roles = subject.has_role(['physician', 'patient', 'nurse_practitioner'])
    roles = [role for role, check in filter(lambda x: x[1], check_roles)]

    return {'roles': roles}


@view_config(route_name='request_rx', renderer='../templates/request_rx.jinja2')
@WebYosai.requires_permission(['rx_request:create'])
def request_rx(context, request):

    rx_request_form = RxRequestForm(request.POST)

    if request.method == "POST" and rx_request_form.validate():
        add_rx_request(request.dbsession, rx_request_form.data['prescription'])

        # request.session.flash('RX Request Submitted.')
        next_url = request.route_url('request_rx')
        return HTTPFound(next_url)
    else:
        current_username = WebYosai.get_current_subject().identifiers.primary_identifier
        results = get_pending_patient_requests(request.dbsession,
                                               current_username).all()

        return {'rx_request_form': rx_request_form,
                'results': results,
                'user': current_username}

@view_config(route_name='rx_portal', renderer='../templates/rx_portal.jinja2')
@WebYosai.requires_role(['physician', 'nurse_practitioner'], logical_operator=any)
def rx_portal(context, request):
    subject = WebYosai.get_current_subject()

    # check_roles looks like:  [('role_name', Boolean), ...]
    check_roles = subject.has_role(['physician', 'nurse_practitioner'])
    roles = [role for role, check in filter(lambda x: x[1], check_roles)]

    return {'roles': roles}


@view_config(route_name='pending_rx', renderer='../templates/pending_rx.jinja2')
@WebYosai.requires_permission(['rx_request:view'])
def pending_rx(context, request):
    if request.method == "POST":
        approve_rx_requests(request.dbsession, request.POST)
        next_url = request.route_url('pending_rx')
        return HTTPFound(next_url)

    else:
        current_username = WebYosai.get_current_subject().identifiers.primary_identifier
        results = get_pending_physician_requests(request.dbsession,
                                                 current_username).all()

        return {'results': results}


@view_config(route_name='write_rx',
             renderer='../templates/write_rx.jinja2')
def write_rx(context, request):

    write_rx_form = WriteRXForm(request.POST, context={'request': request})

    if request.method == 'POST' and write_rx_form.validate():

        medicine = write_rx_form.data['medicine'].id
        perm = 'prescription:write:{0}'.format(medicine)

        current_user = WebYosai.get_current_subject()
        try:
            current_user.check_permission([perm])

        except IdentifiersNotSetException:
            msg = ("Attempting to perform a user-only operation.  The "
                   "current Subject is NOT a user (they haven't been "
                   "authenticated or remembered from a previous login). "
                   "ACCESS DENIED.")
            raise HTTPUnauthorized(msg)

        except AuthorizationException:
            msg = "Access Denied.  Insufficient Permissions."
            raise HTTPForbidden(msg)

        current_username = current_user.identifiers.primary_identifier

        create_rx(request.dbsession,
                  current_username,
                  write_rx_form.data['medicine'],
                  write_rx_form.data['patient'],
                  write_rx_form.data['title'],
                  write_rx_form.data['fill_qty'],
                  write_rx_form.data['num_fills'])

        # When a prescription gets created, a new resource-level permission could be
        # created in the yosai database, allowing resource-level authorization
        # for that new rx. However, time has not yet allowed support for adding new
        # resource to the yosai db.  Adding this to TO-DO.
        #resource = ResourceModel(name=prescription.id)

        next_url = request.route_url('write_rx')
        return HTTPFound(location=next_url)

    return {'write_rx_form': write_rx_form}
