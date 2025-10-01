# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.misc import format_date
from ..utils.helpers import OPERATOR_MAP, one2many_count, many2many_count
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import ValidationError

from logging import getLogger
from pytz import utc
from datetime import datetime


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
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help="The company this record belongs to",
        comodel_name="res.company",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
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
        default=None,
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

    # pylint: disable=locally-disabled, w0212
    date_start = fields.Datetime(
        string="Start date",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_start(),
        help="Start date of an event, without time for full day events",
    )

    def default_start(self):
        now = fields.Datetime.now()
        now = fields.Datetime.context_timestamp(self, now)
        now = now.replace(hour=0, minute=0, second=0)

        return now.astimezone(utc).replace(tzinfo=None)

    # pylint: disable=locally-disabled, w0212
    date_stop = fields.Datetime(
        string="End date",
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_date_stop(),
        help="Stop date of an event, without time for full day events",
    )

    def default_date_stop(self):
        now = fields.Datetime.now()
        now = fields.Datetime.context_timestamp(self, now)
        now = now.replace(hour=23, minute=59, second=59)

        return now.astimezone(utc).replace(tzinfo=None)

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
        default=20,
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
        default=0,
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
