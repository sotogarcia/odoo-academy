# -*- coding: utf-8 -*-
""" AcademyTrainingProgram

This module contains the academy.training.program Odoo model which stores
all training program attributes and behavior.
"""


# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import UserError, ValidationError
from ..utils.helpers import OPERATOR_MAP, one2many_count
from ..utils.helpers import sanitize_code, default_code
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

from logging import getLogger
from uuid import uuid4

CODE_SEQUENCE = "academy.training.program.sequence"

_logger = getLogger(__name__)


class AcademyTrainingProgram(models.Model):
    """This describes the program offered, its modules and training units"""

    _name = "academy.training.program"
    _description = "Academy training program"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "ownership.mixin",
    ]

    _rec_name = "name"
    _order = "name ASC"
    _rec_names_search = ["name", "code", "training_framework_id"]

    _IMMUTABLE_FIELDS = ("program_type", "training_framework_id")

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the training program",
        size=1024,
        translate=True,
        copy=False,
        tracking=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Training Program",
        translate=True,
        copy=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting",
        copy=True,
        tracking=True,
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
        copy=False,
    )

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: default_code(self.env, CODE_SEQUENCE),
        help="Public code or short identifier for the program",
        size=30,
        translate=False,
        copy=False,
        tracking=True,
    )

    # Field program_type and onchange -----------------------------------------

    program_type = fields.Selection(
        string="Program type",
        required=True,
        readonly=True,
        index=True,
        default="training",
        help="Select whether this is a standard training program or a "
        "training support program.",
        selection=[
            ("training", "Training Program"),
            ("support", "Training Support Program"),
        ],
    )

    @api.onchange("program_type")
    def _onchange_program_type_clear_lines(self):
        if self.program_type == "support":
            self.program_line_ids = [(5, 0, 0)]

    training_framework_id = fields.Many2one(
        string="Training framework",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training framework to which this program belongs",
        comodel_name="academy.training.framework",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
        copy=True,
        tracking=True,
    )

    professional_family_id = fields.Many2one(
        string="Professional family",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional family to which this program belongs",
        comodel_name="academy.professional.family",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    @api.onchange("professional_family_id")
    def _onchange_professional_family_id(self):
        self.professional_area_id = None

    professional_area_id = fields.Many2one(
        string="Professional area",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional area to which this program belongs",
        comodel_name="academy.professional.area",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    professional_field_id = fields.Many2one(
        string="Professional field",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional field associated with this program",
        comodel_name="academy.professional.field",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    @api.onchange("professional_field_id")
    def _onchange_professional_field_id(self):
        self.professional_sector_ids = [(5, 0, 0)]

    professional_sector_ids = fields.Many2many(
        string="Professional sectors",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional sectors related to this program",
        comodel_name="academy.professional.sector",
        relation="academy_training_program_professional_sector_rel",
        column1="training_program_id",
        column2="professional_sector_id",
        domain=[],
        context={},
        copy=True,
    )

    qualification_level_id = fields.Many2one(
        string="Qualification level",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Qualification level to which this training program belongs",
        comodel_name="academy.qualification.level",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    attainment_id = fields.Many2one(
        string="Educational attainment",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Minimum educational requirement to access this program",
        comodel_name="academy.educational.attainment",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    general_competence = fields.Text(
        string="General competence",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Overall competence expected after completing the program",
        translate=True,
        copy=True,
    )

    program_line_ids = fields.One2many(
        string="Program lines",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Program lines (modules) included in this program",
        comodel_name="academy.training.program.line",
        inverse_name="training_program_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    # Computed field: program_line_count --------------------------------------

    program_line_count = fields.Integer(
        string="No. of lines",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Computed number of program lines",
        compute="_compute_program_line_count",
        store=True,
        copy=False,
    )

    @api.depends("program_line_ids")
    def _compute_program_line_count(self):
        domain = [("is_section", "=", False)]
        counts = one2many_count(self, "program_line_ids", domain)

        for record in self:
            record.program_line_count = counts.get(record.id, 0)

    training_action_ids = fields.One2many(
        string="Training actions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Training actions (editions) that use this program",
        comodel_name="academy.training.action",
        inverse_name="training_program_id",
        domain=[],
        context={},
        auto_join=False,
        check_company=True,
        copy=False,
    )

    # Computed field: training_action_count -----------------------------------

    training_action_count = fields.Integer(
        string="No. of actions",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Computed number of training actions",
        compute="_compute_training_action_count",
        search="_search_training_action_count",
        copy=False,
    )

    @api.depends("training_action_ids")
    def _compute_training_action_count(self):
        counts = one2many_count(self, "training_action_ids")

        for record in self:
            record.training_action_count = counts.get(record.id, 0)

    @api.model
    def _search_training_action_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "training_action_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # Computed field: hours --------------------------------------------------

    hours = fields.Float(
        string="Hours",
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Total hours computed from linked modules",
        compute="_compute_hours",
        store=True,
        copy=True,
        tracking=True,
    )

    @api.depends("program_line_ids.training_module_id.hours")
    def _compute_hours(self):
        hours_path = "program_line_ids.training_module_id.hours"
        for record in self:
            hours_list = record.mapped(hours_path)
            record.hours = sum(hours_list) if hours_list else 0.0

    # -------------------------- Contraints -----------------------------------

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "Program code must be unique",
        ),
    ]

    @api.constrains("program_type", "program_line_ids")
    def _check_support_program_has_no_lines(self):
        """A Training Support Program cannot have training lines."""
        for rec in self:
            if rec.program_type == "support" and rec.program_line_ids:
                raise ValidationError(
                    _("A Training Support Program cannot have training lines.")
                )

    # ---------------------------- PUBLIC FIELDS ------------------------------

    def update_from_external(self, crud, fieldname, recordset):
        """Observer notify method, will be called by action"""
        self._compute_training_action_count()

    def view_training_actions(self):
        self.ensure_one()

        name = self.env._("Actions: {}").format(self.display_name)

        action_xid = "academy_base.action_training_action_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_program_id": self.id})

        domain = [("training_program_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def view_training_program_lines(self):
        self.ensure_one()

        name = self.env._("Program: {}").format(self.display_name)

        action_xid = "academy_base.action_training_program_line_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_program_id": self.id})

        domain = [("training_program_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    # -- Methods overrides ----------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        sanitize_code(values_list, "upper")
        return super().create(values_list)

    def write(self, values):
        """Overridden method 'write'"""
        values = values or {}

        self._avoid_writing_to_immutable_fields(values)
        sanitize_code(values, "upper")

        return super().write(values)

    def copy(self, default=None):
        self.ensure_one()

        default = dict(default or {})

        if not default.get("name", False):
            name = self.name or _("New training program")
            sufix = uuid4().hex[:8]
            default["name"] = f"{name} ‒ {sufix}"

        new_program = super().copy(default)

        line_default = {"training_program_id": new_program.id}
        for line in self.program_line_ids:
            line.copy(default=line_default)

        return new_program

    def _avoid_writing_to_immutable_field(self, values, field_name):
        self.ensure_one()

        field = self._fields[field_name]
        new = values.get(field_name)
        # Normalizar Many2one a ID para comparar
        if field.type == "many2one":
            old = self[field_name].id or False
            if isinstance(new, models.BaseModel):
                new = new.id
        else:
            old = self[field_name]
        if new != old:
            raise ValidationError(
                _("Field '%s' cannot be modified after saving.") % field.string
            )

    def _avoid_writing_to_immutable_fields(self, values):
        fields_to_check = set(values) & set(self._IMMUTABLE_FIELDS)
        if fields_to_check:
            for record in self:
                for field_name in fields_to_check:
                    record._avoid_writing_to_immutable_field(
                        values, field_name
                    )

        return True
