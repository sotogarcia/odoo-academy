# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class FacilityReservation(models.Model):
    """
    """

    _inherit = ['facility.reservation']

    session_id = fields.Many2one(
        string='Session',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Session to which this facility reservation is related',
        comodel_name='academy.training.session',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=True,
        default=0,
        help='Order of importance of the teacher in the training session'
    )

    _sql_constraints = [
        (
            'UNIQUE_FACILITY_BY_SESSION',
            'UNIQUE(facility_id, session_id)',
            _(u'The facility had already been assigned to the session')
        ),
        (
            'positive_interval',  # Overwrite original
            'CHECK(session_id IS NOT NULL OR (date_start < date_stop))',
            _('Reservation cannot finish before it starts')
        ),
    ]
