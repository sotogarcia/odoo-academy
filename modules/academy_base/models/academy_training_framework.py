# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api, _
from logging import getLogger
from odoo.exceptions import ValidationError
from ..utils.helpers import OPERATOR_MAP, one2many_count
from ..utils.helpers import sanitize_code
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.tools.safe_eval import safe_eval

_logger = getLogger(__name__)


class AcademyTrainingFramework(models.Model):
    _name = "academy.training.framework"
    _description = "Academy training framework"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "ownership.mixin",
    ]

    _order = "name ASC"
    _rec_name = "name"
    _rec_names_search = ["name", "code", "issuing_authority", "legal_code"]

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Regulatory framework name",
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=(
            "Extended notes about scope, applicability, exceptions, and "
            "internal criteria for using this framework in programs and "
            "enrollments."
        ),
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
    )

    code = fields.Char(
        string="Framework Code",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Short, unique-ish code used in URLs/filters",
        translate=False,
    )

    issuing_authority_id = fields.Many2one(
        string="Issuing Authority",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Organization responsible for the framework",
        comodel_name="res.partner",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    training_program_ids = fields.One2many(
        string="Training programs",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Programs governed by this framework",
        comodel_name="academy.training.program",
        inverse_name="training_framework_id",
        domain=[],
        context={},
        auto_join=False,
    )

    training_program_count = fields.Integer(
        string="Training program count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_training_program_count",
        search="_search_training_program_count",
    )

    @api.depends("training_program_ids")
    def _compute_training_program_count(self):
        counts = one2many_count(self, "training_program_ids")

        for record in self:
            record.training_program_count = counts.get(record.id, 0)

    @api.model
    def _search_training_program_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "training_program_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    is_modular = fields.Boolean(
        string="Is modular",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Allows enrollment by module (modular delivery permitted)",
    )

    legal_code = fields.Char(
        string="Legal code",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Short official identifier (e.g., 'LO 3/2022', 'RD 659/2023').",
        translate=False,
    )

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [
        (
            "unique_code",
            "unique(code)",
            "There is already a framework with this code",
        ),
    ]

    # -- Methods overrides ----------------------------------------------------

    @api.model_create_multi
    def create(self, value_list):
        sanitize_code(value_list, "upper")
        return super().create(value_list)

    def write(self, values):
        sanitize_code(values, "upper")
        return super().write(values)

    # -- Public methods -------------------------------------------------------

    def view_training_programs(self):
        self.ensure_one()

        action_xid = "{module}.{name}".format(
            module="academy_base",
            name="action_academy_training_program_act_window",
        )
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_framework_id": self.id})

        domain = [("training_framework_id", "=", self.id)]

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

    # -- Auxiliary methods ----------------------------------------------------
