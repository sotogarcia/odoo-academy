# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.misc import format_date
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import ValidationError

from ..utils.helpers import OPERATOR_MAP, one2many_count
from ..utils.datetime_utils import local_midnight_as_utc
from ..utils.helpers import sanitize_code, default_code

from logging import getLogger
from datetime import datetime
from uuid import uuid4

CODE_SEQUENCE = "academy.training.action.group.sequence"

_logger = getLogger(__name__)


class AcademyTrainingActionGroup(models.Model):
    _name = "academy.training.action.group"
    _description = "Academy training action group"

    _rec_name = "name"
    _order = "name ASC"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "ownership.mixin",
    ]

    _rec_name = "name"
    order = "name, date_start"
    _rec_names_search = ["name", "code", "training_action_id"]

    _check_company_auto = True

    company_id = fields.Many2one(
        string="Company",
        related="training_action_id.company_id",
        store=True,
    )

    name = fields.Char(
        string="Action name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Training Action",
        size=1024,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Training Action",
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
        string="Internal code",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: default_code(self.env, CODE_SEQUENCE),
        help="Enter new internal code",
        size=30,
        translate=False,
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

    date_start = fields.Datetime(
        string="Start date",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_start(),
        help="Start date of an event, without time for full day events",
    )

    def default_start(self):
        today = fields.Date.context_today(self)
        tz_name = self.env.user.tz or self.env.company.partner_id.tz or "UTC"

        return local_midnight_as_utc(
            value=today,
            from_tz=tz_name,
            remove_tz=True,
        )

    date_stop = fields.Datetime(
        string="End date",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Stop date of an event, without time for full day events",
    )

    available_until = fields.Datetime(
        string="Available at",
        required=False,
        readonly=True,
        index=True,
        default=datetime.max,
        help="00:00 the day after, or infinity for open enrolments.",
        compute="_compute_available_until",
        store=True,
    )

    @api.depends("date_stop")
    def _compute_available_until(self):
        infinity = datetime.max

        for record in self:
            if record.date_stop:
                record.available_until = record.date_stop
            else:
                record.available_until = infinity

    # -- Field+onchange: training_action_id -----------------------------------

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.onchange("training_action_id")
    def _onchange_training_action_id(self):
        action = self.training_action_id

        self.active = action.active if action else True
        self.date_start = action.date_start if action else self.default_start
        self.date_stop = action.date_stop if action else None
        self.training_modality_id = (
            action.training_modality_id if action else None
        )

        self.name = self._get_first_available_name()
        self.seating = self._get_available_capacity("seating", 20)
        self.excess = self._get_available_capacity("excess", 25)

    training_program_id = fields.Many2one(
        string="Training program",
        help="Training program will be imparted in this action",
        related="training_action_id.training_program_id",
    )

    action_line_ids = fields.One2many(
        string="Action lines",
        help=(
            "Programme lines included in this training action "
            "(syllabus units/modules to be delivered)."
        ),
        related="training_action_id.action_line_ids",
    )

    action_line_count = fields.Integer(
        string="Action line count",
        related="training_action_id.action_line_count",
    )

    # -- Field+onchange: seating ----------------------------------------------

    seating = fields.Integer(
        string="Seating",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._get_available_capacity("seating", 20),
        help="Maximum number of signups allowed",
    )

    @api.onchange("seating")
    def _onchange_seating(self):
        self.excess = max(self.seating, self.excess)

    excess = fields.Integer(
        string="Excess",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._get_available_capacity("excess", 25),
        help=(
            "Maximum number of students who can be invited to use this "
            "feature at the same time"
        ),
    )

    enrolment_ids = fields.One2many(
        string="Enrolments",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Show the number of enrolments related with the training group",
        comodel_name="academy.training.action.enrolment",
        inverse_name="training_group_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    # -- Computed field: enrolment_count --------------------------------------

    enrolment_count = fields.Integer(
        string="Enrolment count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Show number of enrolments",
        compute="_compute_enrolment_count",
        search="_search_enrolment_count",
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

    # -- Computed field: lifespan ---------------------------------------------

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
    )

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [
        (
            "unique_action_code",
            'UNIQUE("code")',
            "The given group code already exists",
        ),
        (
            "check_date_order",
            'CHECK("date_stop" IS NULL OR "date_start" < "date_stop")',
            "Group start must be earlier than group stop.",
        ),
        (
            "users_greater_or_equal_to_zero",
            "CHECK(seating >= 0)",
            "The number of users must be greater than or equal to zero",
        ),
        (
            "excess_greater_or_equal_to_seating",
            "CHECK(excess >= seating)",
            "The total number of excess users must be greater than or equal to seating users",
        ),
    ]

    @api.constrains("date_start", "date_stop", "training_action_id")
    def _constrains_interval_inside_action(self):
        error_start = _("Group starts before action start.")
        error_stop = _("Group ends after action stop.")
        infinity = fields.Datetime.to_datetime("9999-12-31 23:59:59")

        for record in self:
            date_start = record.date_start
            action = record.training_action_id

            if not date_start or not action:
                continue

            action_start = action.date_start
            action_stop = action.date_stop or infinity

            date_stop = record.date_stop or infinity

            if action_start and date_start < action_start:
                raise ValidationError(error_start)

            if date_stop > action_stop:
                raise ValidationError(error_stop)

    @api.constrains("seating", "excess", "training_action_id")
    def _constrains_action_capacity_totals(self):
        error_seating = _("Sum of groups 'Seating' exceeds action 'Seating'.")
        error_excess = _("Sum of groups 'Excess' exceeds action 'Excess'.")

        for group in self:
            action = group.training_action_id
            if not action:
                continue

            groups = action.training_group_ids

            seat_sum = sum(groups.mapped("seating")) if groups else 0
            excess_sum = sum(groups.mapped("excess")) if groups else 0

            if seat_sum > action.seating:
                raise ValidationError(error_seating)

            if excess_sum > action.excess:
                raise ValidationError(error_excess)

    # -- Auxiliary methods ----------------------------------------------------

    def _get_first_available_name(self):
        self.ensure_one()

        if not self.training_action_id or not self.training_action_id.name:
            return _("New training group")

        action_name = self.training_action_id.name
        other_groups = self.training_action_id.training_group_ids

        if not other_groups:
            return f"{action_name} ‒ A"

        used_names = other_groups.mapped("name")
        for name in [f"{action_name} ‒ {chr(i)}" for i in range(65, 91)]:
            if name not in used_names:
                return name

        return f"{action_name} ‒ {uuid4()}"

    def _get_available_capacity(self, field="seating", default=20):
        result = default

        training_action = self.training_action_id or self._get_m2o_default(
            "academy.training.action", "training_action_id"
        )

        if training_action:
            max_value = getattr(training_action, field, 0)
            max_value = max_value if isinstance(max_value, int) else 0

            print(field, max_value)

            if max_value == 0:
                result = 0
            else:
                training_groups = training_action.training_group_ids
                training_groups = training_groups.filtered(lambda r: r != self)
                values = training_groups.mapped(field)
                print(field, values)
                total_used = sum([v for v in values if isinstance(v, int)])
                result = max_value - total_used

        return result

    def _get_m2o_default(self, model, field):
        model_obj = self.env[model]

        record_id = self.env.context.get(f"default_{field}", False)
        if record_id:
            return model_obj.browse(record_id)

        return model_obj.browse()

    @api.model_create_multi
    def create(self, value_list):
        """Overridden method 'create'"""

        sanitize_code(value_list, "upper")

        return super().create(value_list)

    def write(self, values):
        """Overridden method 'write'"""

        sanitize_code(values, "upper")

        return super().write(values)
