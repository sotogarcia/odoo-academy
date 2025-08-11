# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN
from odoo.tools import safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerAdministrativeRegion(models.Model):

    _name = 'civil.service.tracker.administrative.region'
    _description = u'Civil service tracker administrative region'

    _table = 'cst_administrative_region'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name of the administrative region (e.g., Galicia, Bavaria)',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enable to make this region available; disable to archive it'
    )

    state_ids = fields.One2many(
        string='States',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='List of states or provinces belonging to this region',
        comodel_name='res.country.state',
        inverse_name='administrative_region_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    @api.onchange('country_id')
    def _onchange_country_id(self):
        self.state_ids = None

    state_count = fields.Integer(
        string='State count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Total number of states within the region',
        compute='_compute_state_count'
    )

    @api.depends('state_ids')
    def _compute_state_count(self):
        for record in self:
            record.state_count = len(record.state_ids)

    country_id = fields.Many2one(
        string='Country',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Country to which this region belongs',
        comodel_name='res.country',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
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
