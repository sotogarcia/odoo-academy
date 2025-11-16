# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.training.action Odoo model which stores
all training action attributes and behavior.
"""


from odoo.tools.translate import _
from odoo.tools.misc import format_date

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import AND, OR, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from ..utils.helpers import OPERATOR_MAP, one2many_count, many2many_count
from ..utils.sql_helpers import create_index

from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import ARCHIVED_DOMAIN, INCLUDE_ARCHIVED_DOMAIN
from ..utils.datetime_utils import local_midnight_as_utc
from ..utils.helpers import sanitize_code, default_code

from logging import getLogger
from pytz import utc
from uuid import uuid4
from enum import IntFlag, auto

# from psycopg2 import Error as PsqlError
# from datetime import datetime, date, time, timedelta

_TA_CODE_SEQUENCE = "academy.training.action.sequence"
_TAG_CODE_SEQUENCE = "academy.training.action.group.sequence"
_INFINITY = fields.Datetime.to_datetime("9999-12-31 23:59:59")
_PARENT_EXCLUDE = {"parent_id", "name", "child_ids"}
_CTX_SKIP_PROGRAM = "skip_training_program_replication"


_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingAction(models.Model):
    """The training actions represent several groups of students for the same
    training program
    """

    _name = "academy.training.action"
    _description = "Academy training action"

    _inherit = [
        "ownership.mixin",
        "mail.thread",
        "image.mixin",
        "mail.activity.mixin",
    ]

    _rec_name = "name"
    _order = "parent_path, sequence, name, id"
    _rec_names_search = ["name", "code", "training_program_id"]

    @property
    def shared_keys(self):
        return self.env["academy.training.program"].shared_keys()

    # -- Company dependency: Fields and logic
    # -------------------------------------------------------------------------

    _check_company_auto = True

    company_id = fields.Many2one(
        string="Company",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="The company this record belongs to",
        comodel_name="res.company",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=True,
    )

    # -- Hierarchy: Fields and logic
    # -------------------------------------------------------------------------

    _parent_store = True

    parent_id = fields.Many2one(
        string="Training action",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Parent training action used to group this record.",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=True,
    )

    parent_path = fields.Char(
        string="Parent path",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Path used for efficient ancestors/descendants queries.",
        translate=False,
        copy=False,
    )

    child_ids = fields.One2many(
        string="Training groups",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Children training actions belonging to this record.",
        comodel_name="academy.training.action",
        inverse_name="parent_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    training_group_count = fields.Integer(
        string="No. of groups",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        compute="_compute_training_group_count",
        search="_search_training_group_count",
        copy=False,
    )

    @api.depends("child_ids")
    def _compute_training_group_count(self):
        counts = one2many_count(self, "child_ids")

        for record in self:
            record.training_group_count = counts.get(record.id, 0)

    @api.model
    def _search_training_group_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "child_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    keep_synchronized = fields.Boolean(
        string="Synchronize program",
        required=False,
        readonly=False,
        index=True,
        default=False,
        help=(
            "If enabled, this child action will automatically keep its "
            "training program synchronized with the parent action's program."
        ),
        copy=True,
    )

    # -- Entity fields
    # -------------------------------------------------------------------------

    name = fields.Char(
        string="Action name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the training action",
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
        help="Detailed description of the Training Action",
        translate=True,
        copy=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
        copy=True,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=False,
        default=10,
        help="<Enrolment> priority for new students",
        copy=False,
    )

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Enter new internal code",
        size=30,
        translate=False,
        copy=False,
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

    application_scope_id = fields.Many2one(
        string="Application scope",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.application.scope",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=True,
    )

    professional_category_id = fields.Many2one(
        string="Professional category",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional category",
        comodel_name="academy.professional.category",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=True,
    )

    knowledge_area_ids = fields.Many2many(
        string="Knowledge areas",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related knowledge areas",
        comodel_name="academy.knowledge.area",
        relation="academy_training_action_knowledge_area_rel",
        column1="training_action_id",
        column2="knowledge_area_id",
        domain=[],
        context={},
        copy=True,
    )

    training_modality_id = fields.Many2one(
        string="Training modality",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=(
            "Defines how the training action is delivered, "
            "such as face-to-face, online or blended."
        ),
        comodel_name="academy.training.modality",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=True,
        tracking=True,
    )

    training_methodology_ids = fields.Many2many(
        string="Training methodology",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose training methodologies",
        comodel_name="academy.training.methodology",
        relation="academy_training_action_training_methodology_rel",
        column1="training_action_id",
        column2="training_methodology_id",
        domain=[],
        context={},
        copy=True,
        tracking=True,
    )

    # -- Time interval fields and logic
    # -------------------------------------------------------------------------

    date_start = fields.Datetime(
        string="Start date",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Start date of an event, without time for full day events",
        copy=True,
        tracking=True,
    )

    date_stop = fields.Datetime(
        string="End date",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Stop date of an event, without time for full day events",
        copy=True,
        tracking=True,
    )

    available_until = fields.Datetime(
        string="Available at",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="00:00 the day after, or indefinitely for open enrolments.",
        compute="_compute_available_until",
        search="_search_available_until",
        copy=False,
    )

    @api.depends("date_stop")
    def _compute_available_until(self):
        for record in self:
            if record.date_stop:
                record.available_until = record.date_stop
            else:
                record.available_until = _INFINITY

    @api.model
    def _search_available_until(self, op, val):
        """
        Map filters on the computed 'available_until' to the real 'date_stop'.

        Semantics:
          - available_until is 'date_stop' if set; otherwise it's INFINITY.
          - So:
            >= X or > X -> date_stop >= X (or open)  -> date_stop False OR >= X
            <= X or < X -> date_stop <= X (not open) -> date_stop set AND <= X
            =  X        -> if X == INFINITY -> open; else exact date_stop == X
            != X        -> complement of '=':
                            if X == INFINITY -> date_stop is set (not open)
                            else open OR date_stop != X
        """
        # Normalize incoming value to a datetime when applicable
        dt = val
        if isinstance(dt, str):
            try:
                dt = fields.Datetime.to_datetime(dt)
            except Exception:
                dt = val  # leave as-is for non-datetime ops

        if op in (">=", ">"):
            return ["|", ("date_stop", "=", False), ("date_stop", op, dt)]

        if op in ("<=", "<"):
            return ["&", ("date_stop", "!=", False), ("date_stop", op, dt)]

        if op == "=":
            if dt == _INFINITY:
                return [("date_stop", "=", False)]
            return ["&", ("date_stop", "!=", False), ("date_stop", "=", dt)]

        if op == "!=":
            if dt == _INFINITY:
                return [("date_stop", "!=", False)]
            return ["|", ("date_stop", "=", False), ("date_stop", "!=", dt)]

        if op in ("=", "!=") and val in (False, None):
            return FALSE_DOMAIN if op == "=" else TRUE_DOMAIN

        return TRUE_DOMAIN

    lifespan = fields.Char(
        string="Lifespan",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Start and end dates as a formatted range",
        size=50,
        translate=False,
        compute="_compute_lifespan",
        copy=False,
    )

    @api.depends("date_start", "date_stop")
    @api.depends_context("uid")
    def _compute_lifespan(self):
        for record in self:
            if record.date_start and record.date_stop:
                register_str = format_date(self.env, record.date_start)
                deregister_str = format_date(self.env, record.date_stop)
                record.lifespan = f"{register_str} ‒ {deregister_str}"
            elif record.date_start:
                record.lifespan = format_date(self.env, record.date_start)
            else:
                record.lifespan = ""

    # -- Training program and its attributes
    # -------------------------------------------------------------------------

    training_program_id = fields.Many2one(
        string="Training program",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Training program will be delivered in this action",
        comodel_name="academy.training.program",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=True,
    )

    program_type = fields.Selection(
        string="Program type",
        related="training_program_id.program_type",
        help="Select whether this is a standard training program or a ",
        store=True,
    )

    program_name = fields.Char(
        string="Name",
        related="training_program_id.name",
    )

    program_code = fields.Char(
        string="code",
        related="training_program_id.code",
    )

    training_framework_id = fields.Many2one(
        string="Training Framework",
        related="training_program_id.training_framework_id",
    )

    hours = fields.Float(
        string="hours",
        related="training_program_id.hours",
    )

    professional_family_id = fields.Many2one(
        string="Professional Family",
        related="training_program_id.professional_family_id",
    )

    professional_area_id = fields.Many2one(
        string="Professional Area",
        related="training_program_id.professional_area_id",
    )

    qualification_level_id = fields.Many2one(
        string="Qualification Level",
        related="training_program_id.qualification_level_id",
    )

    attainment_id = fields.Many2one(
        string="Educational Attainment",
        related="training_program_id.attainment_id",
    )

    general_competence = fields.Text(
        string="General Competence",
        related="training_program_id.general_competence",
    )

    professional_field_id = fields.Many2one(
        string="Professional Field",
        related="training_program_id.professional_field_id",
    )

    professional_sector_ids = fields.Many2many(
        string="Professional Sectors",
        related="training_program_id.professional_sector_ids",
    )

    # -- Training program snapshop: fields and logic
    # -------------------------------------------------------------------------

    action_line_ids = fields.One2many(
        string="Action lines",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=(
            "Programme lines included in this training action "
            "(syllabus units/modules to be delivered)."
        ),
        comodel_name="academy.training.action.line",
        inverse_name="training_action_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    action_line_count = fields.Integer(
        string="No. of lines",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        compute="_compute_action_line_count",
        search="_search_action_line_count",
        copy=False,
    )

    @api.depends("action_line_ids")
    def _compute_action_line_count(self):
        domain = [("is_section", "=", False)]
        counts = one2many_count(self, "action_line_ids", domain)

        for record in self:
            record.action_line_count = counts.get(record.id, 0)

    @api.model
    def _search_action_line_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "action_line_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Capacity: fields and logic
    # -------------------------------------------------------------------------

    seats = fields.Integer(
        string="Seating",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Maximum number of sign-ups allowed",
        copy=True,
        tracking=True,
    )

    @api.onchange("seats")
    def _onchange_seats(self):
        for record in self:
            if record.seats and record.seats > record.excess:
                record.excess = record.seats

    excess = fields.Integer(
        string="Excess",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Upper bound of seats that may be admitted (>= Seating).",
        copy=True,
        tracking=True,
    )

    @api.onchange("excess")
    def _onchange_excess(self):
        for record in self:
            if record.excess and record.excess < record.seats:
                record.excess = record.seats

    # -------------------------------------------------------------------------

    enrolment_ids = fields.One2many(
        string="Enrolments",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Show the number of enrolments related with the training action",
        comodel_name="academy.training.action.enrolment",
        inverse_name="training_action_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    enrolment_count = fields.Integer(
        string="No. of enrolments",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Show number of enrolments",
        compute="_compute_enrolment_count",
        search="_search_enrolment_count",
        copy=False,
    )

    @api.depends("enrolment_ids")
    def _compute_enrolment_count(self):
        counts = one2many_count(self, "enrolment_ids")

        for record in self:
            record.enrolment_count = counts.get(record.id, 0)

    @api.model
    def _search_enrolment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "enrolment_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    rollup_enrolment_ids = fields.One2many(
        string="Enrolments (rollup)",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="All enrolments from this action and its direct groups.",
        comodel_name="academy.training.action.enrolment",
        inverse_name="parent_action_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    rollup_enrolment_count = fields.Integer(
        string="No. of enrolments (rollup)",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Show number of enrolments",
        compute="_compute_rollup_enrolment_count",
        search="_search_rollup_enrolment_count",
        copy=False,
    )

    @api.depends("rollup_enrolment_ids")
    def _compute_rollup_enrolment_count(self):
        counts = one2many_count(self, "rollup_enrolment_ids")

        for record in self:
            record.rollup_enrolment_count = counts.get(record.id, 0)

    @api.model
    def _search_rollup_enrolment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "rollup_enrolment_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    current_enrolment_count = fields.Integer(
        string="No. of current enrolments (rollup)",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Show number of enrolments currently active",
        compute="_compute_current_enrolment_count",
        search="_search_current_enrolment_count",
        copy=False,
    )

    @api.depends(
        "rollup_enrolment_ids",
        "rollup_enrolment_ids.register",
        "rollup_enrolment_ids.deregister",
        "rollup_enrolment_ids.active",
    )
    def _compute_current_enrolment_count(self):
        """Compute number of currently active enrolments in the rollup."""
        now = fields.Datetime.now()
        domain = [
            ("active", "=", True),
            ("register", "<=", now),
            "|",
            ("deregister", "=", False),
            ("deregister", ">=", now),
        ]
        counts = one2many_count(self, "rollup_enrolment_ids", domain)

        for record in self:
            record.current_enrolment_count = counts.get(record.id, 0)

    @api.model
    def _search_current_enrolment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        now = fields.Datetime.now()
        domain = [
            ("active", "=", True),
            ("register", "<=", now),
            "|",
            ("deregister", "=", False),
            ("deregister", ">=", now),
        ]
        counts = one2many_count(
            self.search([]), "rollup_enrolment_ids", domain
        )
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Teacher assignment: fields and logic
    # -------------------------------------------------------------------------

    teacher_assignment_ids = fields.One2many(
        string="Teacher assignments",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Teacher assignments; order defines primary.",
        comodel_name="academy.training.teacher.assignment",
        inverse_name="training_action_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    primary_teacher_id = fields.Many2one(
        string="Lead",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Primary teacher (lowest sequence).",
        comodel_name="academy.teacher",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        compute="_compute_primary_teacher_id",
        inverse="_inverse_primary_teacher_id",
        store=True,
        copy=False,
        tracking=True,
    )

    @api.depends(
        "teacher_assignment_ids",
        "teacher_assignment_ids.sequence",
        "teacher_assignment_ids.teacher_id",
        "teacher_assignment_ids.teacher_id.active",
        "teacher_assignment_ids.action_line_id",
    )
    def _compute_primary_teacher_id(self):
        assignment_obj = self.env["academy.training.teacher.assignment"]
        primary_dict = assignment_obj.get_primary(self)

        for record in self:
            record.primary_teacher_id = primary_dict.get(record.id)

    def _inverse_primary_teacher_id(self):
        """When setting a primary teacher:
        - If the teacher already has an assignment in this unit, move it to 1st.
        - Else, overwrite the teacher of the lowest-sequence assignment.
          If there are no assignments yet, create one at sequence=1.
        """
        assignment_obj = self.env["academy.training.teacher.assignment"]
        for record in self:
            teacher = record.primary_teacher_id
            if not record.id:
                continue

            domain = [("training_action_id", "=", record.id)]
            assigns = assignment_obj.search(domain, order="sequence, id")

            if not assigns:
                if teacher:
                    values = {
                        "training_action_id": record.id,
                        "teacher_id": teacher.id,
                        "sequence": 1,
                    }
                    assignment_obj.create(values)
                continue

            if teacher:
                existing = assigns.filtered(lambda a: a.teacher_id == teacher)
                if existing:
                    # take to first place
                    existing.write({"sequence": 0})
                else:
                    # overwrite the assignment with a lower sequence
                    first = assigns[0]
                    first.write({"teacher_id": teacher.id})

                # normalize 1..n
                ordered = assignment_obj.search(domain, order="sequence, id")
                for i, a in enumerate(ordered, start=1):
                    if a.sequence != i:
                        a.sequence = i

    teacher_assignment_count = fields.Integer(
        string="No. of teachers",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_teacher_assignment_count",
        search="_search_teacher_assignment_count",
    )

    @api.depends("teacher_assignment_ids")
    def _compute_teacher_assignment_count(self):
        counts = one2many_count(self, "teacher_assignment_ids")

        for record in self:
            record.teacher_assignment_count = counts.get(record.id, 0)

    @api.model
    def _search_teacher_assignment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "teacher_assignment_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Business fields and logic
    # 1 => Red
    # 2 => Orange
    # 3 => Yellow
    # 4 => Light blue
    # 5 => Dark purple
    # 6 => Salmon pink
    # 7 => Medium blue
    # 8 => Dark blue
    # 9 => Fushia
    # 10 => Green
    # 11 => Purple
    # -------------------------------------------------------------------------

    color = fields.Integer(
        string="Color",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_color",
        copy=False,
    )

    @api.depends("child_ids", "date_stop")
    def _compute_color(self):
        now = fields.Datetime.now()
        for record in self:
            if record.date_stop and record.date_stop < now:
                record.color = 2  # Orange
            elif record.child_ids:
                record.color = 10  # Green
            else:
                record.color = 4  # Light blue

    delivered_action_ids = fields.Many2many(
        string="Delivered actions",
        help=(
            "Includes all child actions if present; otherwise, includes "
            "this training action"
        ),
        required=False,
        readonly=False,
        index=False,
        default=None,
        comodel_name="academy.training.action",
        relation="academy_training_action_delivered_action_rel",
        column1="parent_action_id",
        column2="child_action_id",
        domain=[],
        context={},
        compute="_compute_delivered_action_ids",
        search="_search_delivered_action_ids",
        copy=False,
    )

    @api.depends("parent_id", "child_ids")
    def _compute_delivered_action_ids(self):
        for record in self:
            record.delivered_action_ids = record.child_ids or record

    def _search_delivered_action_ids(self, operator, value):
        base_domain = [("child_ids", "=", False)]

        rec_name_domains = [
            [(field, operator, value)] for field in self._rec_names_search
        ]
        name_domain = OR(rec_name_domains) if rec_name_domains else []

        return AND([base_domain, name_domain])

    student_ids = fields.Many2manyView(
        string="Students",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Students directly or indirectly enrolled in this action.",
        comodel_name="academy.student",
        relation="academy_training_action_student_link",
        column1="training_action_id",
        column2="student_id",
        domain=[],
        context={},
        copy=False,
    )

    student_count = fields.Integer(
        string="No. of students",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_student_count",
        search="_search_student_count",
        copy=False,
    )

    @api.depends(
        "enrolment_ids",
        "rollup_enrolment_ids",
        "enrolment_ids.student_id",
        "rollup_enrolment_ids.student_id",
        "student_ids",
    )
    def _compute_student_count(self):
        counts = many2many_count(self, "student_ids")

        for record in self:
            record.student_count = counts.get(record.id, 0)

    @api.model
    def _search_student_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = many2many_count(self.search([]), "student_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # ------------------------------ CONSTRAINS -------------------------------

    _sql_constraints = [
        (
            "check_date_order",
            'CHECK("date_stop" IS NULL OR "date_start" < "date_stop")',
            "End date must be greater than start date",
        ),
        (
            "users_greater_or_equal_to_zero",
            "CHECK(seats >= 0)",
            "The number of users must be greater than or equal to zero",
        ),
    ]

    # Funcionará si los campos vuelve a ser almacenados. Ahora NO lo son.
    # (
    #     "prevent_enrolment_group_mix",
    #     "CHECK (COALESCE(training_group_count, 0) = 0 "
    #     "OR COALESCE(enrolment_count, 0) = 0)",
    #     "An action with groups cannot have direct enrolments, and an action "
    #     "with direct enrolments cannot have groups.",
    # ),

    @api.constrains("enrolment_ids", "child_ids", "parent_id")
    def _check_enrolment_group_conflict(self):
        """Enforce consistency between enrolments and training groups.

        It forbids adding groups under actions with enrolments,
        enrolling in actions whose parent already has groups, mixing
        groups and enrolments on a single action, and creating children
        under support-type actions.
        """
        case_1 = _(
            "You cannot create or assign a training group under "
            "an action that already has student enrolments.\n\n"
            "Remove the enrolments from the parent action first."
        )
        case_2 = _(
            "You cannot enrol students in a training action whose "
            "parent already contains training groups.\n\n"
            "Enrol them in one of the existing groups instead."
        )
        case_3 = _(
            "A training action cannot have both direct student "
            "enrolments and associated training groups.\n\n"
            "Remove either the enrolments or the groups before "
            "proceeding."
        )
        case_4 = _("A support service cannot have child support services.")

        for record in self:
            parent = record.parent_id or self.env["academy.training.action"]

            # --- Case 1: the parent already has enrolments -> cannot add child
            if parent and parent.enrolment_ids:
                raise ValidationError(case_1)

            # --- Case 2: the parent already has child groups -> cannot enrol
            if record.enrolment_ids and parent and parent.child_ids:
                raise ValidationError(case_2)

            # --- Case 3: the record itself is a parent (top-level action)
            # It cannot have both enrolments and groups at the same time.
            if record.enrolment_ids and record.child_ids:
                raise ValidationError(case_3)

            # --- Case 4: the record is not a training action and has children
            if record.program_type == "support" and record.child_ids:
                raise ValidationError(case_4)

    @api.constrains("parent_id")
    def _check_no_cycle(self):
        """Prevent recursive hierarchies."""
        message = _("You cannot create a recursive hierarchy.")
        if self._has_cycle("parent_id"):
            raise ValidationError(message)

    @api.constrains("seats", "excess", "parent_id", "child_ids")
    def _check_aggregated_capacity(self):
        """Validate group capacity against parent capacity.

        Ensures that the sum of seats and excess across all child
        actions does not exceed the corresponding limits defined on the
        parent action.
        """
        fields_to_check = {
            "seats": _("Total seats"),
            "excess": _("Total excess"),
        }

        message = _(
            "Capacity Overrun: The total sum of %s across all groups (%s) "
            "exceeds the limit set on the main action (%s)."
        )

        for record in self:
            parent = record.parent_id or record
            if not parent.seats and not parent.excess:
                continue

            children = parent.child_ids
            if not children:
                continue

            for field_name, field_label in fields_to_check.items():
                p_value = parent[field_name]
                c_value = sum(children.mapped(field_name))

                if p_value < c_value:
                    raise ValidationError(
                        message % (field_label, c_value, p_value)
                    )

    @api.constrains("date_start", "date_stop", "parent_id", "child_ids")
    def _check_aggregated_interval(self):
        """Validate group date interval against parent interval.

        Ensures that all child actions start on or after the parent
        start date and end on or before the parent end date (or the
        synthetic infinity bound when open-ended).
        """
        pattern_start = _(
            "The group(s) start date ({child}) cannot be before the main "
            "action's start date ({parent})."
        )
        pattern_stop = _(
            "The group(s) end date ({child}) cannot be after the main "
            "action's end date ({parent})."
        )

        for record in self:
            parent = record.parent_id or record
            children = parent.child_ids
            if not children:
                continue

            parent_start = parent.date_start
            parent_stop = parent.date_stop or _INFINITY

            child_start = min(children.mapped("date_start"))
            if child_start < parent_start:
                raise ValidationError(
                    pattern_start.format(
                        child=child_start.strftime(DATETIME_FORMAT),
                        parent=parent_start.strftime(DATETIME_FORMAT),
                    )
                )

            child_stops = children.mapped(lambda r: r.date_stop or _INFINITY)
            child_stop = max(child_stops)
            if child_stop > parent_stop:
                raise ValidationError(
                    pattern_stop.format(
                        child=child_stop.strftime(DATETIME_FORMAT),
                        parent=parent_stop.strftime(DATETIME_FORMAT),
                    )
                )

    # -- Overridden methods
    # -------------------------------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        parent_action = self._get_default_parent_training_action(defaults)
        parent_action = parent_action.exists()
        if parent_action:
            parent_action._patch_defaults_on_child(defaults, fields_list)
        else:
            self._patch_defaults_on_parent(defaults)

        return defaults

    def _auto_init(self):
        result = super()._auto_init()

        table = self._table
        code_fields = ["company_id", "LOWER(code)", "COALESCE(parent_id, 0)"]
        create_index(
            env=self.env,
            table_name=table,
            fields=code_fields,
            unique=True,
            name=f"{table}_code_uniq",
            method="btree",
        )

        return result

    @api.model_create_multi
    def create(self, values_list):
        """Create records: inherit from parent, sanitize code, sync, enrols."""

        self._fill_from_parent(values_list)

        sanitize_code(values_list, "upper")
        self._prevent_use_student_link(values_list)

        records = super().create(values_list)

        if not self.env.context.get(_CTX_SKIP_PROGRAM, False):
            no_prog = records.filtered(lambda rec: not rec.action_line_ids)
            no_prog.synchronize(optional=True, remove_mismatches=True)

        records.update_enrolments()

        return records

    def write(self, values):
        """Overridden method 'write'"""
        sanitize_code(values, "upper")
        self._prevent_use_student_link(values)

        result = super().write(values)

        self.update_enrolments()

        return result

    def copy(self, default=None):
        default = dict(default or {})

        if not default.get("name", False):
            name = self.name or _("New training action")
            sufix = uuid4().hex[:8]
            default["name"] = f"{name} ‒ {sufix}"

        action_id = default.get("training_action_id") or self.id
        if "teacher_assignment_ids" not in default:
            self._copy_global_teacher_assignments(default, action_id)

        self_ctx = self.with_context({_CTX_SKIP_PROGRAM: True})
        new_action = super(AcademyTrainingAction, self_ctx).copy(default)

        line_default = {
            "training_action_id": new_action.id,
            "training_program_id": new_action.training_program_id.id,
        }
        for line in self.action_line_ids:
            line.copy(default=line_default)

        group_default = dict(parent_id=new_action.id)
        for training_group in self.child_ids:
            training_group.copy(default=group_default)

        return new_action

    # --------------------------- PUBLIC METHODS ------------------------------

    def view_students(self):
        self.ensure_one()

        name = self.env._("Students: {}").format(self.display_name)

        action_xid = "academy_base.action_student_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        domain = [("id", "in", self.student_ids.ids)]

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

    def view_teacher_assignments(self):
        self.ensure_one()

        name = self.env._("Teachers: {}").format(self.display_name)

        action_xid = "academy_base.action_teacher_assignment_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_action_id": self.id})

        domain = [("training_action_id", "=", self.id)]

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

    def view_training_action_groups(self):
        self.ensure_one()

        name = self.env._("Groups: {}").format(self.display_name)

        action_xid = "academy_base.action_training_action_group_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_parent_id": self.id})

        domain = [("parent_id", "=", self.id)]
        views = [(v.view_id.id, v.view_mode) for v in act_wnd.view_ids]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "views": views,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def view_action_lines(self):
        self.ensure_one()

        name = self.env._("Program: {}").format(self.display_name)

        action_xid = "academy_base.action_training_action_line_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_action_id": self.id})

        domain = [("training_action_id", "=", self.id)]

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

    def update_enrolments(self, force=False):
        for record in self:
            enrol_set = record.enrolment_ids
            target = enrol_set.filtered(
                lambda r: r.date_start < record.date_start
            )

            target.write(
                {"date_start": fields.Datetime.to_string(record.date_start)}
            )

            if record.date_stop:
                target = enrol_set.filtered(
                    lambda r: r.date_stop and r.date_stop > record.date_stop
                )
                target.write(
                    {"date_stop": fields.Datetime.to_string(record.date_stop)}
                )

    def view_enrolments(self):
        self.ensure_one()

        name = self.env._("Enrolments: {}").format(self.display_name)

        act_xid = "academy_base.action_training_action_enrolment_act_window"
        action = self.env.ref(act_xid)

        parent_action_id = self.parent_id.id if self.parent_id else self.id

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update(
            {
                "default_training_action_id": self.id,
                "default_parent_action_id": parent_action_id,
            }
        )

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [("training_action_id", "=", self.id)]])

        action_values = {
            "name": name,
            "type": action.type,
            "help": action.help,
            "domain": domain,
            "context": ctx,
            "res_model": action.res_model,
            "target": action.target,
            "view_mode": action.view_mode,
            "search_view_id": action.search_view_id.id,
        }

        return action_values

    def view_rollup_enrolments(self):
        self.ensure_one()

        name = self.env._("Enrolments: {}").format(self.display_name)

        act_xid = "academy_base.action_training_action_enrolment_act_window"
        action = self.env.ref(act_xid)

        parent_action_id = self.parent_id.id if self.parent_id else self.id
        training_action_id = self.id if not self.child_ids else None

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update(
            {
                "default_training_action_id": training_action_id,
                "default_parent_action_id": parent_action_id,
            }
        )

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [("parent_action_id", "=", self.id)]])

        action_values = {
            "name": name,
            "type": action.type,
            "help": action.help,
            "domain": domain,
            "context": ctx,
            "res_model": action.res_model,
            "target": action.target,
            "view_mode": action.view_mode,
            "search_view_id": action.search_view_id.id,
        }

        return action_values

    def copy_program_image(self):
        for record in self:
            if not record.training_program_id:
                continue

            if not record.training_program_id.image_1920:
                continue

            record.image_1920 = record.training_program_id.image_1920
            record.image_1024 = record.training_program_id.image_1024
            record.image_512 = record.training_program_id.image_512
            record.image_256 = record.training_program_id.image_256
            record.image_128 = record.training_program_id.image_128

    @api.model
    def join_allowed_companies(self):
        allowed_ids = self._context.get(
            "allowed_company_ids", self.env.company.ids
        )

        return ", ".join([str(item) for item in allowed_ids])

    def fetch_with_enrolled(
        self, students=None, point_in_time=None, archived=False
    ):
        """Return actions having enrolments matching the given filters.

        This method searches enrolments
        (``academy.training.action.enrolment``) using the provided
        filters and returns the related training actions
        (``academy.training.action``). When ``self`` is non-empty, the
        search is restricted to actions in ``self``.

        Args:
            students (Any, optional): Student filter for the enrolments.
                It is passed to :func:`create_domain_for_ids` as the
                value for ``student_id`` and may be a recordset, a
                single id or an iterable of ids. When falsy, this
                filter is omitted.
            point_in_time (Any, optional): Temporal filter for the
                enrolments. It is passed to
                :func:`create_domain_for_interval` to build a domain on
                the ``register``/``deregister`` interval. When falsy,
                this filter is omitted.
            archived (bool | None, optional): Archive behaviour:

                * ``False`` (default): use the standard Odoo behaviour
                  (only active records).
                * ``True``: restrict to archived enrolments.
                * ``None``: include both active and archived
                  enrolments.

        Returns:
            recordset: ``academy.training.action`` records that have at
            least one enrolment matching the computed domain. If no
            filters match, an empty recordset is returned.
        """
        training_action_set = self.env["academy.training.action"]

        domains = []

        if students:
            domain = create_domain_for_ids("student_id", students)
            domains.append(domain)

        if self:
            domain = create_domain_for_ids("training_action_id", self)
            domains.append(domain)

        if point_in_time:
            domain = create_domain_for_interval(
                "register", "deregister", point_in_time
            )
            domains.append(domain)

        if archived is None:
            domains.append(INCLUDE_ARCHIVED_DOMAIN)
        elif archived is True:
            domains.append(ARCHIVED_DOMAIN)

        if domains:
            enrolment_obj = self.env["academy.training.action.enrolment"]
            enrolment_set = enrolment_obj.search(AND(domains))
            training_action_set = enrolment_set.mapped("training_action_id")

        return training_action_set

    def synchronize(
        self, *, optional=True, remove_mismatches=True, changes_only=False
    ):
        """Synchronize parent actions with training programs, and child actions
        with their respective parents.

        This helper triggers two synchronization flows:

        * For parent actions (without ``parent_id``), it uses
          ``academy.training.program.synchronize.wizard`` so each
          parent synchronizes its lines from its training program.
        * For child actions (with ``parent_id``), it uses
          ``academy.training.action.synchronize.wizard`` so each group
          synchronizes its lines from its parent action.

        Args:
            optional (bool): If False, skip creating optional lines in
                both synchronization flows.
            remove_mismatches (bool): If True, remove target lines that
                no longer match any source line.
            changes_only (bool): If False, perform a full synchronization,
                ignoring ``needs_synchronization`` flags and forcing all
                related lines to be updated.
                If True, each wizard runs in incremental mode, updating only
                those lines that are marked as needing synchronization or whose
                source line is flagged as changed.

        Returns:
            recordset: ``academy.training.action.line`` records that
                were created or updated.
        """
        action_line_obj = self.env["academy.training.action.line"]
        result_set = action_line_obj.browse()
        if not self:
            return result_set

        # 1. Synchronize non child actions from their related training program
        wizard_obj = self.env["academy.training.program.synchronize.wizard"]
        parent_set = self.filtered(lambda record: not record.parent_id)
        wizard_args = {
            "optional": optional,
            "remove_mismatches": remove_mismatches,
            "synchronize_groups": False,
            "target_set": parent_set,
            "changes_only": changes_only,
        }
        result_set |= wizard_obj.synchronize_training_actions(**wizard_args)

        # 2. Synchronize child actions from their parent training action
        wizard_obj = self.env["academy.training.action.synchronize.wizard"]
        child_set = self.filtered(lambda rec: rec.parent_id)
        wizard_args = {
            "optional": optional,
            "remove_mismatches": remove_mismatches,
            "target_set": child_set,
            "changes_only": changes_only,
        }
        result_set |= wizard_obj.synchronize_training_groups(**wizard_args)

        return result_set

    # Maintenance tasks
    # -------------------------------------------------------------------------

    @api.model
    def training_action_synchronize_task(self):
        """Run the scheduled training action synchronization task."""
        action_line_obj = self.env["academy.training.action.line"]

        _logger.info("Training action synchronization task started.")

        action_obj = self.env["academy.training.action"]
        action_domain = [("keep_synchronized", "=", True)]
        action_set = action_obj.search(action_domain)
        if not action_set:
            _logger.debug(
                "Training action synchronization: no actions to process."
            )
            return action_line_obj.browse()

        _logger.debug(
            "Training action synchronization: %d action(s) will be processed.",
            len(action_set),
        )
        result_set = action_set.synchronize(
            optional=True,
            remove_mismatches=True,
            changes_only=True,
        )

        _logger.info(
            "Training action synchronization: resetting flags on "
            "program and action lines."
        )
        self._reset_needs_synchronization_attribute(action_set, result_set)

        _logger.info(
            "Training action synchronization task finished: %d line(s) "
            "synchronized.",
            len(result_set),
        )

        return result_set

    def _reset_needs_synchronization_attribute(self, action_set, result_set):
        """Reset needs_synchronization flags for lines and programs in scope."""
        if not action_set:
            return

        values = {"needs_synchronization": False}

        action_line_domain = [
            ("needs_synchronization", "=", True),
            ("training_action_id", "in", action_set.ids),
        ]
        program_ids = action_set.mapped("training_program_id").ids

        action_line_obj = self.env["academy.training.action.line"]
        action_line_obj = action_line_obj.with_context(active_test=False)
        action_line_set = action_line_obj.search(action_line_domain)
        if action_line_set:
            action_line_set.write(values)

        if not program_ids:
            return

        program_line_domain = [
            ("needs_synchronization", "=", True),
            ("training_program_id", "in", program_ids),
        ]
        program_line_obj = self.env["academy.training.program.line"]
        program_line_obj = program_line_obj.with_context(active_test=False)
        program_line_set = program_line_obj.search(program_line_domain)
        if program_line_set:
            program_line_set.write(values)

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _eval_domain(domain):
        """Evaluate a domain expresion (str, False, None, list or tuple) an
        returns a valid domain

        Arguments:
            domain {mixed} -- domain expresion

        Returns:
            mixed -- Odoo valid domain. This will be a tuple or list
        """

        if domain in [False, None]:
            domain = []
        elif not isinstance(domain, (list, tuple)):
            try:
                domain = safe_eval(domain)
            except Exception:
                domain = []

        return domain

    def _copy_global_teacher_assignments(self, default, training_action_id):
        if isinstance(training_action_id, models.BaseModel):
            training_action_id = training_action_id.id

        glogal_assignments = self.teacher_assignment_ids.filtered(
            lambda r: not r.action_line_id
        )

        o2m_ops = [(5, 0, 0)]
        for assign in glogal_assignments:
            values = {
                "training_action_id": training_action_id,
                "teacher_id": assign.teacher_id.id,
            }
            o2m_ops.append((0, 0, values))

        default["teacher_assignment_ids"] = o2m_ops

    @staticmethod
    def _prevent_use_student_link(values_list):
        if not values_list:
            pass
        elif isinstance(values_list, list):
            for values in values_list:
                if "student_ids" in values:
                    del values["student_ids"]
        elif isinstance(values_list, dict) and "student_ids" in values_list:
            del values_list["student_ids"]

    @api.model
    def _batch_read_parent_data(self, values_list):
        """Build mapping from parent ids to converted values."""
        if not values_list or not isinstance(values_list, (list, tuple)):
            return {}

        parent_ids = {
            vals.get("parent_id")
            for vals in values_list
            if vals.get("parent_id")
        }

        if not parent_ids:
            return {}

        program_obj = self.env["academy.training.program"]
        shared_keys = program_obj.shared_keys

        self_ctx = self.with_context(active_test=False)
        parents = self_ctx.browse(list(parent_ids))

        parent_data = {}
        for parent in parents:
            raw_values = {key: parent[key] for key in shared_keys}
            converted_values = parent._convert_to_write(raw_values)
            parent_data[parent.id] = converted_values

        return parent_data

    def _fill_from_parent(self, values_list):
        """Inherit parent's values (incl. O2M/M2M with copy=True)."""
        if not values_list or not isinstance(values_list, (list, tuple)):
            return

        parent_data = self._batch_read_parent_data(values_list)
        if not parent_data:
            return

        parent_ids = {
            values.get("parent_id")
            for values in values_list
            if values.get("parent_id")
        }

        parent_domain = [("id", "in", list(parent_ids))]
        parent_context = dict(active_test=False)
        parent_obj = self.env[self._name].with_context(parent_context)
        parent_set = parent_obj.search(parent_domain)

        program_by_parent = {
            parent.id: parent.training_program_id.id
            for parent in parent_set
            if parent.training_program_id
        }

        for values in values_list:
            parent_id = values.get("parent_id")
            if not parent_id:
                continue

            program_id = program_by_parent.get(parent_id)
            if program_id:
                values["training_program_id"] = program_id

            pvals = parent_data.get(parent_id, {}) or {}
            for key, val in pvals.items():
                if key in _PARENT_EXCLUDE:
                    continue
                values.setdefault(key, val)

    @api.model
    def _patch_defaults_on_parent(self, defaults):
        defaults.setdefault("company_id", self.env.company.id)
        defaults.setdefault("code", default_code(self.env, _TA_CODE_SEQUENCE))
        defaults.setdefault("date_start", self._default_start())
        defaults.setdefault("seats", 20)
        defaults.setdefault("excess", 20)

    def _patch_defaults_on_child(self, defaults, fields_list):
        self.ensure_one()

        defaults.setdefault("code", default_code(self.env, _TAG_CODE_SEQUENCE))

        if "name" not in defaults:
            group_name = self._first_available_group_name()
            defaults["name"] = group_name

        seats, excess = self._available_capacity()
        if "seats" not in defaults:
            defaults["seats"] = seats
        if "seats" not in defaults or defaults.get("excess", 0) < seats:
            defaults["excess"] = max(seats, excess)

        parent_values = self.copy_data(default=None)[0] or {}
        fields_list = fields_list or parent_values.keys()
        for key, value in parent_values.items():
            if key in _PARENT_EXCLUDE:
                continue
            if key in fields_list:
                defaults.setdefault(key, value)

    def _get_default_parent_training_action(self, values=None):
        action_obj = self.env["academy.training.action"]

        parent_id = (values or {}).get("parent_id")
        if not parent_id:
            parent_id = self.env.context.get("default_parent_id")

        if parent_id:
            return action_obj.with_context(active_test=False).browse(parent_id)

        return action_obj.browse()

    def _first_available_group_name(self):
        self.ensure_one()

        parent = self.parent_id or self

        action_name = parent.name or self.env._("New training action")
        other_groups = parent.child_ids.filtered(lambda r: r != self)

        if not other_groups:
            return f"{action_name} ‒ A"

        used_names = set(other_groups.mapped("name"))
        for name in [f"{action_name} ‒ {chr(i)}" for i in range(65, 91)]:
            if name not in used_names:
                return name

        return f"{action_name} ‒ {uuid4().hex[:6].upper()}"

    def _available_capacity(self):
        self.ensure_one()

        parent = self.parent_id or self
        others = parent.child_ids.filtered(lambda r: r != self)

        seats = sum((v or 0) for v in others.mapped("seats"))
        excess = sum((v or 0) for v in others.mapped("excess"))

        cap_s = max(0, (parent.seats or 0) - seats)
        cap_e = max(cap_s, (parent.excess or 0) - excess)

        return cap_s, cap_e

    def _default_start(self):
        today = fields.Date.context_today(self)
        tz_name = self.env.user.tz or self.env.company.partner_id.tz or "UTC"

        return local_midnight_as_utc(
            value=today,
            from_tz=tz_name,
            remove_tz=True,
        )
