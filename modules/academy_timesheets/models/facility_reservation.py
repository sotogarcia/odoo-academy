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

    _name = 'facility.reservation'
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

    # @api.model
    # def create(self, values):
    #     """ Overridden method 'create'
    #     """

    #     parent = super(FacilityReservation, self)
    #     reservation = parent.create(values)

    #     if values.get('session_id', False):
    #         reservation.message_change_thread(reservation.session_id)

    #     return reservation

    # def write(self, values):
    #     """ Overridden method 'write'
    #     """

    #     parent = super(FacilityReservation, self)
    #     result = parent.write(values)

    #     for reservation in self:
    #         if reservation.session_id:
    #             reservation.message_change_thread(reservation.session_id)
    #         elif 'session_id' in values.keys():
    #             reservation.message_change_thread(reservation)

    #     return result
