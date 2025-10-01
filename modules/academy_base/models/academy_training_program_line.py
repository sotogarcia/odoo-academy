# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from ..utils.helpers import sanitize_code
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, many2many_count


from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingProgramLine(models.Model):
    _name = "academy.training.program.line"
    _description = "Academy training program line"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "ownership.mixin",
    ]

    _rec_name = "name"
    _order = "sequence ASC"
    _rec_names_search = ["name", "code"]

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name of the program line; usually the module or block title",
        size=1024,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the line content, scope and objectives",
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
        string="Code",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Official or internal code for this program line",
        size=30,
        translate=False,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Defines the order in which modules appear inside the program",
    )

    comment = fields.Html(
        string="Internal notes",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=(
            "Private notes for staff only. Not shown to students, "
            "not exported, and excluded from printed reports."
        ),
        sanitize=True,
        sanitize_attributes=False,
        strip_style=True,
        translate=False,
    )

    optional = fields.Boolean(
        string="Optional",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Mark if this line is optional/elective for the learner",
    )

    hours = fields.Float(
        string="Hours",
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Nominal duration of the line in hours",
    )

    training_program_id = fields.Many2one(
        string="Training program",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training program this line belongs to",
        comodel_name="academy.training.program",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    training_module_id = fields.Many2one(
        string="Training module",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Module or block linked to this program line",
        comodel_name="academy.training.module",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    @api.onchange("training_module_id")
    def _onchange_training_module_id(self):
        if self.training_module_id:
            self.hours = self.training_module_id.hours
        else:
            self.hours = 0.0

    # competency_unit_ids = fields.Many2many(
    #     string="Competence Standards (ECP)",
    #     required=False,
    #     readonly=False,
    #     index=True,
    #     default=None,
    #     help=("Professional Competence Standards (ECP) linked to unit"),
    #     comodel_name="academy.competency.unit",
    #     relation="academy_training_program_line_competency_unit_rel",
    #     column1="program_line_id",
    #     column2="competency_unit_id",
    #     domain=[],
    #     context={},
    # )

    # -- Computed field: competency_unit_count --------------------------------

    # competency_unit_count = fields.Integer(
    #     string="Competence Standard count",
    #     required=True,
    #     readonly=True,
    #     index=False,
    #     default=0,
    #     help=False,
    #     compute="_compute_competency_unit_count",
    #     search="_search_competency_unit_count",
    # )

    # @api.depends("competency_unit_ids")
    # def _compute_competency_unit_count(self):
    #     counts = many2many_count(self, "competency_unit_ids")

    #     for record in self:
    #         record.competency_unit_count = counts.get(record.id, 0)

    # @api.model
    # def _search_competency_unit_count(self, operator, value):
    #     if value is True:
    #         return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
    #     if value is False:
    #         return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

    #     cmp_func = OPERATOR_MAP.get(operator)
    #     if not cmp_func:
    #         return FALSE_DOMAIN  # unsupported operator

    #     counts = many2many_count(self.search([]), "competency_unit_ids")
    #     matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

    #     return [("id", "in", matched)] if matched else FALSE_DOMAIN

    is_section = fields.Boolean(
        string="Is section",
        required=False,
        readonly=False,
        index=True,
        default=False,
        help="If checked, this record is a visual section/separator",
    )

    @api.onchange("is_section")
    def _onchange_is_section(self):
        if self.is_section:
            self.training_module_id = None

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [
        (
            "code_unique",
            "UNIQUE(code)",
            "Module code must be unique",
        ),
        (
            "non_negative_hours",
            "CHECK(hours >= 0)",
            "Hours must be a non-negative number",
        ),
        # (
        #     "unique_module_by_program",
        #     "UNIQUE(training_program_id, training_module_id)",
        #     "The module cannot be duplicated in the same training program",
        # ),
        # (
        #     "section_xor_training",
        #     """CHECK(
        #         COALESCE(is_section, FALSE)
        #         <>
        #         (training_module_id IS NOT NULL)
        #     )""",
        #     "Line must be either a section (no training) or a training item.",
        # ),
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

    def view_current_record(self):
        self.ensure_one()

        action_xid = "academy_base.action_training_program_line_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": self.name,
            "view_mode": "form",
            "domain": [],
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
            "res_id": self.id,
            "views": [(False, "form")],
        }

        return serialized
