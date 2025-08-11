# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerEmploymentGroup(models.Model):

    _name = 'civil.service.tracker.employment.group'
    _description = u'Civil service tracker employment group'

    _table = 'cst_employment_group'

    _rec_name = 'name'
    _order = 'employment_scheme_id ASC, sequence ASC, name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Group or sublevel of employment (e.g. A1, C2, Group IV)',
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Optional description providing additional context',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Indicates whether this administrative scope is currently active'
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=True,
        default=0,
        help='Defines display order; lower values indicate higher importance'
    )

    employment_scheme_id = fields.Many2one(
        string='Employment scheme',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Scheme or system that defines the general employment framework',
        comodel_name='civil.service.tracker.employment.scheme',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    service_position_ids = fields.One2many(
        string='Service position',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Service position associated with this employment group',
        comodel_name='civil.service.tracker.service.position',
        inverse_name='employment_group_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    service_position_count = fields.Integer(
        string='Service position count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of service position assigned to this employment group',
        compute='_compute_service_position_count'
    )

    @api.depends('service_position_ids')
    def _compute_service_position_count(self):
        for record in self:
            record.service_position_count = len(record.service_position_ids)

    @api.depends('service_position_ids')
    def _compute_service_position_count(self):
        for record in self:
            record.service_position_count = len(record.service_position_ids)

    def name_get(self):
        result = []
        
        for record in self:
            name_parts = [record.name]
            
            if record.employment_scheme_id:
                name_parts.insert(0, record.employment_scheme_id.name)
            
            name = ' - '.join(name_parts)
            
            result.append((record.id, name))
        
        return result
