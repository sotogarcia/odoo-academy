# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerOfferQuickOfferWizardLine(models.TransientModel):

    _name = 'civil.service.tracker.quick.offer.wizard.line'
    _description = u'Civil service tracker offer batch creation wizard line'

    _table = 'cst_quick_offer_wizard_line'

    _rec_name = 'id'
    _order = 'id DESC'

    wizard_id = fields.Many2one(
        string='Wizard',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Parent wizard for batch public offer creation',
        comodel_name='civil.service.tracker.quick.offer.wizard',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False
    )

    contract_type_id = fields.Many2one(
        string='Contract type',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Type of employment contract (e.g. civil servant, labor staff)',
        comodel_name='civil.service.tracker.contract.type',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False
    )


    access_type_id = fields.Many2one(
        string='Access type',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Type of access to the position (e.g. internal promotion)',
        comodel_name='civil.service.tracker.access.type',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False
    )

    selection_method_id = fields.Many2one(
        string='Selection method',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Method used to select candidates (e.g. exam, merit-based)',
        comodel_name='civil.service.tracker.selection.method',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False
    )

    service_position_id = fields.Many2one(
        string='Service position',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=('Service position associated with this position '
              '(e.g. Legal Corps)'),
        comodel_name='civil.service.tracker.service.position',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False
    )

    vacancy_type_id = fields.Many2one(
        string='Vacancy type',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Position category (e.g. Free Turn, Promotion)',
        comodel_name='civil.service.tracker.vacancy.type',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False,
        track_visibility='onchange'
    )

    position_quantity = fields.Integer(
        string='Number of positions',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Total number of positions available for this type'
    )

    @api.constrains('position_quantity')
    def _check_positive_quantity(self):
        message = 'Position quantity must be zero or greater.'
        
        for line in self:
            if line.position_quantity < 0:
                raise ValidationError(message)
