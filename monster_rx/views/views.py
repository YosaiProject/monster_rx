from forms import LoginForm
from pyramid.view import view_config

from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from yosai.core import (
    AuthenticationException,
    UsernamePasswordToken,
)


@view_config(route_name='login', renderer='../templates/login.jinja2')
def login(request):

    login_form = LoginForm(request.POST, context={'request': request})

    if request.method == "POST" and login_form.validate():

        authc_token = UsernamePasswordToken(username=login_form.username.data,
                                            password=login_form.password.data)

        try:
            subject = request.subject
            subject.login(authc_token)

            next_url = request.route_url('home')
            return HTTPFound(location=next_url)

        except AuthenticationException:
            request.session.flash('Invalid Login Credentials.')
            return {'form': login_form}

    else:
        return {'form': login_form}


# requires_user
@view_config(route_name='home', renderer='../templates/home.jinja2')
def home(request):
    subject = request.subject
    check_roles = subject.has_roles(['doctor', 'pharmacist', 'patient'])

    # check_roles looks like:  [('role_name', Boolean), ...]
    roles = [role for role, check in filter(lambda x: x[1], check_roles)]
