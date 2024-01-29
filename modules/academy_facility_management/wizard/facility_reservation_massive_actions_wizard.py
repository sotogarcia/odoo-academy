# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from odoo.addons.academy_base.utils.record_utils import get_active_records
from odoo.addons.academy_base.utils.record_utils import single_or_default
from odoo.addons.academy_base.utils.datetime_utils import now_o_clock

from logging import getLogger
from datetime import datetime

_logger = getLogger(__name__)


class AcademyFacilityReservationMassiveActionsWizard(models.TransientModel):
    """ Allow user to update training action
    """

    _name = 'facility.reservation.massive.actions.wizard'
    _inherit = 'facility.reservation.massive.actions.wizard'

    update_training_action_id = fields.Boolean(
        string='Update training action',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to update related training action'
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def _serialize_update_values(self):
        """ Appends training action id to values dictionary
        Notes:
            - Parent method already invokes ``ensure_one`` method.
        """

        parent = super(AcademyFacilityReservationMassiveActionsWizard, self)
        values = parent._serialize_update_values()

        if self.update_training_action_id:
            values['training_action_id'] = self.training_action_id.id

        return values
