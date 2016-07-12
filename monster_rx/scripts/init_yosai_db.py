import os
import sys
import transaction
import datetime
from datetime import timedelta, datetime

from sqlalchemy import case, func, distinct
from passlib.context import CryptContext

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from pyramid.scripts.common import parse_vars

from yosai_alchemystore import (
    init_engine,
    init_session,
    Base,
)
    
from yosai_alchemystore.models.models import (
    CredentialModel,
    UserModel,
    DomainModel,
    ActionModel,
    ResourceModel,
    PermissionModel,
    RoleModel,
    role_membership,
    role_permission,
)

from ..models import (
    get_engine,
    get_session_factory,
    get_tm_session,
)

from ..models import (
    RxRenewalRequest,
    User,
    Medicine,
    Prescription,
)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)

    engine = get_engine(settings)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        # yes, the user model is redundant but I ran out of time making this
        users = [UserModel(first_name='Bubzy', last_name='Monster', identifier='bubzy'),
                 UserModel(first_name='Maxter', last_name='Monster', identifier='maxter'),
                 UserModel(first_name='Bubba', last_name='Monster', identifier='bubba'),
                 UserModel(first_name='Moozy', last_name='Monster', identifier='drmoozy')]

        domains = [DomainModel(name='prescription')]

        actions = [ActionModel(name='write'),
                   ActionModel(name='request'),
                   ActionModel(name='approve'),
                   ActionModel(name='deny')]

        roles = [RoleModel(title='patient'), 
                 RoleModel(title='physician')]

        dbsession.add_all(users + roles + domains + actions)


users = dict((user.first_name+'_'+user.last_name, user) for user in session.query(UserModel).all())
domains = dict((domain.name, domain) for domain in session.query(DomainModel).all())
actions = dict((action.name, action) for action in session.query(ActionModel).all())
resources = dict((resource.name, resource) for resource in session.query(ResourceModel).all())
roles = dict((role.title, role) for role in session.query(RoleModel).all())

thirty_from_now = datetime.datetime.now() + datetime.timedelta(days=30)

cc = CryptContext(schemes=['bcrypt_sha256'])
password = cc.encrypt('letsgobowling')

credentials = [CredentialModel(user_id=user.pk_id, 
                          credential=password,
                          expiration_dt=thirty_from_now) for user in users.values()]
dbsession.add_all(credentials)


perm1 = PermissionModel(domain=domains['money'],
                   action=actions['write'],
                   resource=resources['bankcheck_19911109069'])

perm2 = PermissionModel(domain=domains['money'],
                   action=actions['deposit'])

perm3 = PermissionModel(domain=domains['money'],
                   action=actions['access'],
                   resource=resources['ransom'])

perm4 = PermissionModel(domain=domains['leatherduffelbag'],
                   action=actions['transport'],
                   resource=resources['theringer'])

perm5 = PermissionModel(domain=domains['leatherduffelbag'],
                   action=actions['access'],
                   resource=resources['theringer'])

perm6 = PermissionModel(domain=domains['money'],
                   action=actions['withdrawal'])

perm7 = PermissionModel(action=actions['bowl'])

perm8 = PermissionModel(action=actions['run'])  # I dont know!?

dbsession.add_all([perm1, perm2, perm3, perm4, perm5, perm6, perm7, perm8])

bankcustomer = roles['bankcustomer']
courier = roles['courier']
tenant = roles['tenant']
landlord = roles['landlord']
thief = roles['thief']

bankcustomer.permissions.extend([perm2, perm7, perm8])
courier.permissions.extend([perm4, perm7, perm8])
tenant.permissions.extend([perm1, perm7, perm8])
thief.permissions.extend([perm3, perm4, perm5, perm7, perm8])
landlord.permissions.extend([perm6, perm7, perm8])

thedude = users['Jeffrey_Lebowski']
thedude.roles.extend([bankcustomer, courier, tenant])

walter = users['Walter_Sobchak']
walter.roles.extend([bankcustomer, courier])

marty = users['Marty_Houston']
marty.roles.extend([bankcustomer, landlord])

larry = users['Larry_Sellers']
larry.roles.extend([bankcustomer, thief])  # yes, I know, it's not confirmed

jackie = users['Jackie_Treehorn']
jackie.roles.extend([bankcustomer, thief])  # karl may be working for him-- close enough

karl = users['Karl_Hungus']
karl.roles.extend([bankcustomer, thief])

dbsession.commit()

dbsession.close()
