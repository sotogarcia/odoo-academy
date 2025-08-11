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


class CivilServiceTrackerAdministrationType(models.Model):

    _name = 'civil.service.tracker.administration.type'
    _description = u'Civil service tracker administration type'

    _table = 'cst_administration_type'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        translate='Name of the type (e.g., State, Region, Local)'
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
        help='Indicates whether this administrative type is currently active'
    )

    administration_scope_id = fields.Many2one(
        string='Administration scope',
        required=True,
        index=True,
        ondelete='cascade',
        readonly=False,
        default=None,
        help="Scope of the administration (e.g. state, regional, local)",
        comodel_name='civil.service.tracker.administration.scope',
        domain=[],
        context={},
        auto_join=False,
    )

    region_required = fields.Boolean(
        string='Region required',
        related='administration_scope_id.region_required',
        help="Whether administrative region must be set for this scope.",
        readonly='True',
        store=True
    )

    public_administration_ids = fields.One2many(
        string='Public administrations',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='civil.service.tracker.public.administration',
        inverse_name='administration_type_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
