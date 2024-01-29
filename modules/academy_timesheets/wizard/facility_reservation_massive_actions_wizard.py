# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class TimesheetsFacilityReservationMassiveActionsWizard(models.TransientModel):
    """ Allo user to perform a choosen action over multiple facility
    reservation records.
    """

    _name = 'facility.reservation.massive.actions.wizard'
    _inherit = 'facility.reservation.massive.actions.wizard'

    def _dynamic_action_selection(self):
        parent = super(TimesheetsFacilityReservationMassiveActionsWizard, self)
        result = parent._dynamic_action_selection()

        new_option = ('detach', _('Detach from training'))
        result.append(new_option)

        return result

    def perform_action_detach(self):
        for record in self:
            if not record.target_reservation_ids:
                continue

            record.target_reservation_ids.detach_from_training()
