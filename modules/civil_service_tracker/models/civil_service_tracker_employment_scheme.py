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


class CivilServiceTrackerEmploymentScheme(models.Model):
    _name = "civil.service.tracker.employment.scheme"
    _description = "Civil service tracker employment scheme"

    _table = "cst_employment_scheme"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name of the employment scheme",
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

    employment_group_ids = fields.One2many(
        string="Groups",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="civil.service.tracker.employment.group",
        inverse_name="employment_scheme_id",
        domain=[],
        context={},
        auto_join=False,
    )

    employment_group_count = fields.Integer(
        string="Group count",
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=False,
        compute="_compute_employment_group_count",
    )

    @api.depends("employment_group_ids")
    def _compute_employment_group_count(self):
        for record in self:
            record.employment_group_count = len(record.employment_group_ids)

    public_administration_ids = fields.Many2many(
        string="Public administration",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="civil.service.tracker.employment.scheme",
        relation="cst_public_administration_employment_scheme_rel",
        column1="employment_scheme_id",
        column2="public_administration_id",
        domain=[],
        context={},
    )

    public_administration_count = fields.Integer(
        string="Public administration count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_public_administration_count",
    )

    @api.depends("public_administration_ids")
    def _compute_public_administration_count(self):
        for record in self:
            record.public_administration_count = len(
                record.public_administration_ids
            )

    group_label = fields.Char(
        string="Group label",
        required=False,
        readonly=False,
        index=False,
        default="Group",
        help="Label used to refer to employment groups in this scheme",
        translate=True,
    )

    def view_public_administrations(self):
        self.ensure_one()

        action_xid = (
            "civil_service_tracker."
            "action_civil_services_public_administration_act_window"
        )
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_employment_scheme_id": self.id})

        administration_ids = self.public_administration_ids.ids
        domain = [("id", "in", administration_ids)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": act_wnd.name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    official_journal_url = fields.Char(
        string="Official journal URL",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Link to the official journal or legal source of publication",
        translate=False,
        copy=False,
    )
