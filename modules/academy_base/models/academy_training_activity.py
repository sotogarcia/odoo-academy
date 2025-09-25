# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module contains the academy.training.activity Odoo model which stores
all training activity attributes and behavior.
"""


# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count, many2many_count
from ..utils.helpers import sanitize_code
from odoo.tools import safe_eval
from odoo.tools.translate import _

from logging import getLogger
from uuid import uuid4

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingActivity(models.Model):
    """This describes the activity offered, its modules and training units"""

    _name = "academy.training.activity"
    _description = "Academy training activity"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "ownership.mixin",
    ]

    _rec_name = "name"
    _order = "name ASC"
    _rec_names_search = ["name", "code", "training_framework_id"]

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=1024,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new description",
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
        index=True,
        default=None,
        help="Reference code that identifies the program",
        size=30,
        translate=False,
    )

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
        ondelete="cascade",
        auto_join=False,
    )

    professional_family_id = fields.Many2one(
        string="Professional family",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional family to which this activity belongs",
        comodel_name="academy.professional.family",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
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
        help="Professional area to which this activity belongs",
        comodel_name="academy.professional.area",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    professional_field_id = fields.Many2one(
        string="Professional field",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional field",
        comodel_name="academy.professional.field",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
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
        help="Choose related professional sectors",
        comodel_name="academy.professional.sector",
        relation="academy_training_activity_professional_sector_rel",
        column1="training_activity_id",
        column2="professional_sector_id",
        domain=[],
        context={},
    )

    qualification_level_id = fields.Many2one(
        string="Qualification level",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Qualification level to which this activity belongs",
        comodel_name="academy.qualification.level",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    attainment_id = fields.Many2one(
        string="Educational attainment",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Choose related educational attainment",
        comodel_name="academy.educational.attainment",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    general_competence = fields.Text(
        string="General competence",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=(
            "Describes the most significant professional functions of the "
            "professional profile"
        ),
        translate=True,
    )

    program_line_ids = fields.One2many(
        string="Program lines",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="academy.training.program.line",
        inverse_name="training_program_id",
        domain=[],
        context={},
        auto_join=False,
    )

    program_line_count = fields.Integer(
        string="Program line count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_program_line_count",
        search="_search_program_line_count",
    )

    @api.depends("program_line_ids")
    def _compute_program_line_count(self):
        counts = one2many_count(self, "program_line_ids")

        for record in self:
            record.program_line_count = counts.get(record.id, 0)

    @api.model
    def _search_program_line_count(self, operator, value):
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = many2many_count(self.search([]), "program_line_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    training_action_ids = fields.One2many(
        string="Training actions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Training actions in which this activity is imparted",
        comodel_name="academy.training.action",
        inverse_name="training_activity_id",
        domain=[],
        context={},
        auto_join=False,
        check_company=True,
    )

    token = fields.Char(
        string="Token",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: str(uuid4()),
        help="Unique token used to track this answer",
        translate=False,
        copy=False,
        tracking=True,
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    hours = fields.Float(
        string="Hours",
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Total number of hours of length for the activity",
        # compute="_compute_hours",
        # search="_search_hours",
    )

    # pylint: disable=W0212
    training_action_count = fields.Integer(
        string="Number of training actions",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_training_action_count",
        search="_search_training_action_count",
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

    # -------------------------- Contraints -----------------------------------

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "Module code must be unique",
        ),
    ]

    # ---------------------------- PUBLIC FIELDS ------------------------------

    # pylint: disable=locally-disabled, W0613
    def update_from_external(self, crud, fieldname, recordset):
        """Observer notify method, will be called by action"""
        self._compute_training_action_count()

    def show_training_actions(self):
        self.ensure_one()

        return {
            "model": "ir.actions.act_window",
            "type": "ir.actions.act_window",
            "name": _("Training actions"),
            "res_model": "academy.training.action",
            "target": "current",
            "view_mode": "kanban,list,form",
            "domain": [("training_activity_id", "=", self.id)],
            "context": {"default_training_activity_id": self.id},
        }

    def view_training_program_lines(self):
        self.ensure_one()

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
            "name": act_wnd.name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    # -- Methods overrides ----------------------------------------------------

    @api.model_create_multi
    def create(self, value_list):
        sanitize_code(value_list, "upper")
        return super().create(value_list)

    def write(self, values):
        """Overridden method 'write'"""
        values = values or {}
        sanitize_code(values, "upper")

        user = self.env.user
        if not user.has_group("academy_base.academy_group_manager"):
            values.pop("training_action_count", False)
            values.pop("training_module_count", False)

        parent = super(AcademyTrainingActivity, self)
        result = parent.write(values)

        return result
