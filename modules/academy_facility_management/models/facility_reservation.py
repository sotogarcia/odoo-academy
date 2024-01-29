# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS

from logging import getLogger


_logger = getLogger(__name__)


class FacilityReservation(models.Model):
    """ Extends facility reservation to allow to asign a training action
    """

    _name = 'facility.reservation'
    _inherit = 'facility.reservation'

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

    has_training_action = fields.Boolean(
        string='Has training action',
        required=False,
        readonly=True,
        index=False,
        default=False,
        help='Check it when the reservation has a related training action',
        compute='_compute_has_training_action',
        search='_search_has_training_action'
    )

    @api.depends('training_action_id')
    def _compute_has_training_action(self):
        for record in self:
            record.has_training_action = bool(record.training_action_id)

    @api.model
    def _search_has_training_action(self, operator, value):
        value = bool(value)  # Prevents None

        if value is True:
            operator = NEGATIVE_TERM_OPERATORS(operator)
            value = not value

        return [('training_action_id', operator, value)]

    def _name_get(self):
        """ When the facility reservation has a related training action it will
        be shown the training action name as display name, otherwise parent
        ``name_get`` method will be used to compute final display name.

        This is a private user-defined method, Not to be confused with the
        ``name_get`` starndard public method.

        Returns:
            str: name will be shown in GUI
        """

        self.ensure_one()

        if self.training_action_id and not self.name:
            name = self.training_action_id.action_name
        else:
            parent = super(FacilityReservation, self)
            name = parent._name_get()

        return name
