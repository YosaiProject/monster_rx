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
                 UserModel(first_name='Moozy', last_name='Monster', identifier='drmoozy')]

        domains = [DomainModel(name='prescription'),
                   DomainModel(name='rx_request')]

        actions = [ActionModel(name='create'),
                   ActionModel(name='approve'),
                   ActionModel(name='deny'),
                   ActionModel(name='view')]

        resources = [ResourceModel(name='1')]  # the first prescription pk_id

        roles = [RoleModel(title='patient'), 
                 RoleModel(title='physician')]

        dbsession.add_all(users + roles + domains + actions)

        users = dict((user.identifier, user) for user in dbsession.query(UserModel).all())
        domains = dict((domain.name, domain) for domain in dbsession.query(DomainModel).all())
        actions = dict((action.name, action) for action in dbsession.query(ActionModel).all())
        roles = dict((role.title, role) for role in dbsession.query(RoleModel).all())

        thirty_from_now = datetime.datetime.now() + datetime.timedelta(days=30)

        cc = CryptContext(schemes=['bcrypt_sha256'])
        password = cc.encrypt('M0nsterRX')

        credentials = [CredentialModel(user_id=user.pk_id, 
                                       credential=password,
                                       expiration_dt=thirty_from_now) for user in users.values()]
        dbsession.add_all(credentials)

        perm1 = PermissionModel(domain=domains['prescription'],
                                action=actions['write'])
        
        perm2 = PermissionModel(domain=domains['rx_request'],
                                action=actions['create'])

        perm3 = PermissionModel(domain=domains['rx_request'],
                                action=actions['approve'])
        
        perm4 = PermissionModel(domain=domains['rx_request'],
                                action=actions['deny'])
        
        perm5 = PermissionModel(domain=domains['rx_request'],
                                action=actions['view'])
        
        perm6 = PermissionModel(domain=domains['prescription'],
                                action=actions['create'],
                                resource=resources['1'])  # resource-level perm for first rx

        dbsession.add_all([perm1, perm2, perm3, perm4, perm5, perm6])

        patient = roles['patient']
        physician = roles['physician']

        # associate permissions with roles
        patient.permissions.append([perm2])  # a patient can create an rx_request
        physician.permissions.extend([perm1, perm3, perm4, perm6])

        # assign the users to roles
        drmoozy = users['drmoozy']
        drmoozy.roles.extend([physician, patient])

        bubzy = users['bubzy']
        bubzy.roles.append([patient])
