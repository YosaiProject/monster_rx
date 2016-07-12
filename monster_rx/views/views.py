from forms import LoginForm
from pyramid.view import view_config

from pyramid.httpexceptions import HTTPFound

from yosai.core import (
    AuthenticationException,
    UsernamePasswordToken,
    Yosai,
)


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
    subject = Yosai.get_current_subject()
    check_roles = subject.has_roles(['doctor', 'patient'])

    # check_roles looks like:  [('role_name', Boolean), ...]
    roles = [role for role, check in filter(lambda x: x[1], check_roles)]

    return {'roles': roles}


# @view_config(route_name='process_rx_reqs', renderer='../templates/process_rx_reqs.jinja2')
#def process_rx_reqs(request):
    # view or approve/deny
#    pass


#@view_config(route_name='create_rx', renderer='../templates/create_rx.jinja2')
#def create_rx(request):
    # when a prescription gets created, a new resource-level permission gets
    # created


#@view_config(route_name='request_rx_renewal', renderer='../templates/request_rx_renewal.jinja2')
#def request_rx_renewal(request):

#    rx_refill_form = RxRefillForm(request.POST, context={'request': request})
    # requires an rx_id to refill
    # get patient's prescriptions from db
    # if request method = POST, the patient has submitted a form request that
    # contains the prescription that the refill request will be submitted for
    # otherwise, display a prescription refill request form
