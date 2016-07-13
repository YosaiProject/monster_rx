import os
import sys
import transaction
from datetime import timedelta, datetime

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from pyramid.scripts.common import parse_vars

from ..models.meta import Base
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

        users = [User(username='bubzy', fullname='Bubzy Monster'),
                 User(username='drmoozy', fullname='Dr. Moozy Monster')]

        meds = [Medicine(title='Cinnamon Jelly Bean'),
                Medicine(title='Blueberry Jelly Bean'),
                Medicine(title='Vanilla Jelly Bean'),
                Medicine(title='Cherry Jelly Bean'),
                Medicine(title='Strawberry Jelly Bean')]

        rxs = [Prescription(physician=users[2],
                            patient=users[0],
                            medicine=meds[0],
                            title='Cinnamon JB, taken 3 times daily.',
                            fill_qty=90,
                            num_fills=5),
               Prescription(physician=users[2],
                            patient=users[0],
                            medicine=meds[1],
                            title='Blueberry JB, taken 3 times daily.',
                            fill_qty=90,
                            num_fills=5),
               Prescription(physician=users[3],
                            patient=users[1],
                            medicine=meds[2],
                            title='Vanilla JB, taken 2 times daily.',
                            fill_qty=90,
                            num_fills=5),
               Prescription(physician=users[3],
                            patient=users[1],
                            medicine=meds[3],
                            title='Cherry JB, taken once daily.',
                            fill_qty=90,
                            num_fills=5),
               Prescription(physician=users[3],
                            patient=users[1],
                            medicine=meds[4],
                            title='Strawberry JB, taken once daily.',
                            fill_qty=30,
                            num_fills=0,
                            created_dt=(datetime.now() - timedelta(days=30)))]

        rx_req = [RxRenewalRequest(status='requested', rx=rxs[4], requestor=users[0])]

        dbsession.add_all(users + meds + rxs + rx_req)
