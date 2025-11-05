# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerAdministrationScope(models.Model):
    _name = "civil.service.tracker.administration.scope"
    _description = "Civil service tracker administration scope"

    _table = "cst_administration_scope"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        translate="Name of the scope (e.g., State, Region, Local)",
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Optional description providing additional context",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Indicates whether this administrative scope is currently active",
    )

    region_required = fields.Boolean(
        string="Region required",
        required=False,
        readonly=False,
        index=True,
        default=False,
        help=False,
    )

    administration_type_ids = fields.One2many(
        string="Administration types",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="civil.service.tracker.administration.type",
        inverse_name="administration_scope_id",
        domain=[],
        context={},
        auto_join=False,
    )

    public_administration_ids = fields.One2many(
        string="Public administrations",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="civil.service.tracker.public.administration",
        inverse_name="administration_scope_id",
        domain=[],
        context={},
        auto_join=False,
    )
