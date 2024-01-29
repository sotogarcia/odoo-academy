# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class FacilityReservationScheduler(models.Model):
    """ Extends facility reservation scheduler to allow to choose a training
        action will be related with the created facility reservacions.
    """

    _name = 'facility.reservation.scheduler'
    _inherit = 'facility.reservation.scheduler'

    training_action_id = fields.Many2one(
        string='Training action',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Training action for which the facility will be reserved',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):
        self.name = self.training_action_id.action_name

    def _build_reservation_values(self):
        """ Appends training action id to the values dictionary

        Returns:
            dict: values dictionary will be used to create or update sessions
        """

        parent = super(FacilityReservationScheduler, self)

        # Parent method invokes ``self.ensure_one`` method
        values = parent._build_reservation_values()

        training_action_id = self.training_action_id.id
        values.update(training_action_id=training_action_id)

        return values
