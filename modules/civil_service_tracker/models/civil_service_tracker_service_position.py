# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.misc import str2bool
from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerServicePosition(models.Model):
    _name = "civil.service.tracker.service.position"
    _description = "Civil service tracker service position"

    _table = "cst_service_position"

    _rec_name = "name"
    _order = "name ASC"

    _rec_names_search = ["name", "short_name"]

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name of the specific service position (e.g. Health Corps)",
        translate=True,
    )

    short_name = fields.Char(
        string="Short name",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Commonly used or internal short name, e.g., "PSG".',
        translate=True,
        copy=False,
    )

    position_label = fields.Char(
        string="Position label",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=(
            "Label to display instead of the generic field name 'Service "
            "position', such as 'Corps', 'Category', 'Professional group', "
            "etc."
        ),
        translate=True,
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

    public_administration_id = fields.Many2one(
        string="Administration",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Public administration with its own position structure",
        comodel_name="civil.service.tracker.public.administration",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    available_employment_group_ids = fields.One2many(
        string="Available groups",
        readonly=True,
        related=(
            "public_administration_id."
            "employment_scheme_ids.employment_group_ids"
        ),
    )

    @api.onchange("public_administration_id")
    def _onchange_public_administration_id(self):
        for record in self:
            record.employment_group_id = None
            if not record.position_label:
                label = record.public_administration_id.position_label
                record.position_label = label

    employment_group_id = fields.Many2one(
        string="Group",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Employment group (e.g., C1, C2, Group A)",
        comodel_name="civil.service.tracker.employment.group",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    contract_type_id = fields.Many2one(
        string="Contract type",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Type of employment contract (e.g. civil servant, labor staff)",
        comodel_name="civil.service.tracker.contract.type",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.depends("short_name", "name")
    @api.depends_context("lang")
    def _compute_display_name(self):
        config = self.env["ir.config_parameter"].sudo()
        param_name = "civil_service_tracker.display_process_short_name"

        raw_value = config.get_param(param_name, default="False")
        use_short = str2bool(raw_value)

        for record in self:
            if use_short and record.short_name:
                record.display_name = record.short_name
            else:
                record.display_name = record.name

    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value

        if value is None:
            return False

        return str(value).strip().lower() in ("1", "true", "yes", "on")
