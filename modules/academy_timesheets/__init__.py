# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from . import models
from . import report
from . import wizard
from . import controllers

from odoo import api, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


DROP_SESSION_RESERVATION_TRIGGER = '''
    DROP TRIGGER IF EXISTS
        academy_training_session_facility_reservation_time_interval
        ON academy_training_session;
'''

CREATE_SESSION_RESERVATION_TRIGGER = '''
    CREATE TRIGGER
        academy_training_session_facility_reservation_time_interval
        AFTER INSERT OR UPDATE OF date_start, date_stop
        ON academy_training_session FOR EACH ROW
        EXECUTE PROCEDURE
        academy_training_session_facility_reservation_time_interval()
'''

DROP_SESSION_RESERVATION_TRIGGER_FUNCTION = '''
    DROP FUNCTION IF EXISTS
        academy_training_session_facility_reservation_time_interval;
'''

CREATE_SESSION_RESERVATION_TRIGGER_FUNCTION = '''
    CREATE OR REPLACE FUNCTION
        academy_training_session_facility_reservation_time_interval()
    RETURNS TRIGGER AS
    $BODY$
        BEGIN
                UPDATE facility_reservation AS fr
                SET date_start = ats.date_start,
                    date_stop = ats.date_stop
            FROM
                academy_training_session AS ats
            WHERE
                ats."id" = fr.session_id;
            RETURN NEW;

        END;
    $BODY$ LANGUAGE plpgsql;
'''


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.debug('Executing academy_timesheets.pre_init_hook')

    # Following two lines should not be necessary, but they can help prevent
    # potential problems.
    env.cr.execute(DROP_SESSION_RESERVATION_TRIGGER)
    env.cr.execute(DROP_SESSION_RESERVATION_TRIGGER_FUNCTION)

    env.cr.execute(CREATE_SESSION_RESERVATION_TRIGGER_FUNCTION)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.debug('Executing academy_timesheets.post_init_hook')

    env.cr.execute(CREATE_SESSION_RESERVATION_TRIGGER)

    # weekdays = env['facility.weekday'].sudo().search([])
    # for action in env['academy.training.action'].sudo().search([]):
    #     date_base = action.start.date()
    #     weekday_domain = [('sequence', '=', action.start.isoweekday())]
    #     weekday_set = weekdays.sudo().filtered_domain(weekday_domain)

    #     action.write({
    #         'date_base': date_base,
    #         'weekday_ids': [(6, 0, [weekday_set[0].id])]
    #     })


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.debug('Executing academy_timesheets.uninstall_hook')

    env.cr.execute(DROP_SESSION_RESERVATION_TRIGGER)
    env.cr.execute(DROP_SESSION_RESERVATION_TRIGGER_FUNCTION)


# def post_load(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})
