# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from re import search
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _
from odoo.osv.expression import AND, OR, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import UserError, MissingError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.exceptions import ValidationError
from odoo.addons.academy_base.utils.helpers import (
    OPERATOR_MAP,
    one2many_count,
    many2many_count,
)

from datetime import timedelta, datetime, date, time
from dateutil.relativedelta import relativedelta
from logging import getLogger
import re
import calendar
import pytz

_INTERVAL_RE = re.compile(r"^(day|week|month|year)(?:(?::(\d+))|([+-]\d+))?$")


_logger = getLogger(__name__)


class AcademyTrainingSession(models.Model):
    """Temporarily delimited phase or act in which part of a training action
    takes place
    """

    _name = "academy.training.session"
    _description = "Academy training session"

    _inherit = ["mail.thread", "ownership.mixin"]

    _rec_name = "id"
    _order = "date_start ASC"
    _rec_names_search = [
        "training_action_id",
        "action_line_id",
    ]

    _check_company_auto = True

    # -- Entity fields
    # -------------------------------------------------------------------------

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
        help="Enables/disables the record",
    )

    state = fields.Selection(
        string="State",
        required=True,
        readonly=False,
        index=True,
        default="draft",
        help="Current session status",
        selection=[("draft", "Draft"), ("ready", "Ready")],
        groups="academy_base.academy_group_technical",
        tracking=True,
    )

    action_line_id = fields.Many2one(
        string="Competency unit",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Related program unit",
        comodel_name="academy.training.action.line",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    validate = fields.Boolean(
        string="Validate",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="If checked, the event date range will be checked before saving",
    )

    program_type = fields.Selection(
        string="Program type",
        required=True,
        readonly=False,
        index=True,
        default="training",
        help=False,
        selection=[
            ("training", "Training Program"),
            ("support", "Training Support Program"),
        ],
    )

    # Training action information
    # -------------------------------------------------------------------------

    training_action_id = fields.Many2one(
        string="Training action",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Related training action",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    @api.onchange("training_action_id")
    def _onchange_training_action_id(self):
        for record in self:
            record.action_line_id = None

    company_id = fields.Many2one(
        string="Company",
        help="The company this record belongs to",
        related="training_action_id.company_id",
        store=True,
    )

    training_program_id = fields.Many2one(
        string="Training program",
        related="training_action_id.training_program_id",
    )

    allow_overlap = fields.Boolean(
        string="Allow overlap",
        related="training_action_id.allow_overlap",
        store=True,
    )

    # Facility reservation information
    # -------------------------------------------------------------------------

    reservation_ids = fields.One2many(
        string="Reservations",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Related facility reservations",
        comodel_name="facility.reservation",
        inverse_name="session_id",
        domain=[],
        context={"default_state": "requested"},
        auto_join=False,
        tracking=True,
        copy=False,
    )

    reservation_count = fields.Integer(
        string="Reservation count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Total number of facility reservations required for this session",
        compute="_compute_reservation_count",
        search="_search_reservation_count",
    )

    @api.depends("reservation_ids")
    def _compute_reservation_count(self):
        counts = one2many_count(self, "reservation_ids")

        for record in self:
            record.reservation_count = counts.get(record.id, 0)

    @api.model
    def _search_reservation_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "reservation_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    facility_ids = fields.Many2manyView(
        string="Facility",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="facility.facility",
        relation="facility_reservation",
        column1="session_id",
        column2="facility_id",
        domain=[],
        context={},
    )

    primary_facility_id = fields.Many2one(
        string="Primary facility",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Main facility where the training session will take place",
        comodel_name="facility.facility",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        compute="_compute_primary_facility_id",
        store=True,
        tracking=True,
    )

    @api.depends(
        "reservation_ids",
        "reservation_ids.sequence",
        "reservation_ids.facility_id",
        "reservation_ids.active",
        "reservation_ids.facility_id.active",
    )
    def _compute_primary_facility_id(self):
        """Assign the first reservation per session by sequence, then id."""
        for record in self:
            record.primary_facility_id = False

        reservation_obj = self.env["facility.reservation"]
        reservations = reservation_obj.search(
            [
                ("session_id", "in", self.ids),
                ("active", "=", True),
                ("facility_id.active", "=", True),
            ],
            order="session_id, sequence NULLS LAST, id",
        )

        # Take the first reservation per session (already stably ordered)
        first_by_session = {}
        for reservation in reservations:
            session_id = reservation.session_id.id
            if session_id not in first_by_session:
                first_by_session[session_id] = reservation

        for session in self:
            reservation = first_by_session.get(session.id)
            if reservation and reservation.facility_id:
                session.primary_facility_id = reservation.facility_id
            else:
                session.primary_facility_id = False

    primary_complex_id = fields.Many2one(
        string="Primary complex",
        related="primary_facility_id.complex_id",
        store=True,
    )

    # -- Teacher information
    # -------------------------------------------------------------------------

    teacher_assignment_ids = fields.One2many(
        string="Teacher assignments",
        required=True,
        readonly=False,
        index=True,
        default=None,  # lambda self: self.default_teacher_assignment_ids(),
        help=False,
        comodel_name="academy.training.session.teacher.assignment",
        inverse_name="session_id",
        domain=[],
        context={},
        auto_join=False,
        tracking=True,
        copy=False,
    )

    teacher_ids = fields.Many2manyView(
        string="Teachers",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Teachers who teach this training session",
        comodel_name="academy.teacher",
        relation="academy_training_session_teacher_assignment",
        column1="session_id",
        column2="teacher_id",
        domain=[],
        context={},
        copy=False,
    )

    teacher_count = fields.Integer(
        string="Teacher count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Total number of related teachers",
        compute="_compute_teacher_count",
    )

    @api.depends("teacher_ids")
    def _compute_teacher_count(self):
        counts = many2many_count(self, "teacher_ids")

        for record in self:
            record.teacher_count = counts.get(record.id, 0)

    @api.model
    def _search_reservation_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = many2many_count(self.search([]), "teacher_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    primary_teacher_id = fields.Many2one(
        string="Primary instructor",
        required=False,
        readonly=True,
        index=True,
        help="Ultimately responsible for providing instruction",
        default=False,
        comodel_name="academy.teacher",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        compute="_compute_primary_teacher_id",
        store=True,
        tracking=True,
    )

    @api.depends(
        "teacher_assignment_ids",
        "teacher_assignment_ids.sequence",
        "teacher_assignment_ids.teacher_id",
        "teacher_assignment_ids.teacher_id.active",
    )
    def _compute_primary_teacher_id(self):
        for record in self:
            record.primary_teacher_id = False

        assignment_obj = self.env[
            "academy.training.session.teacher.assignment"
        ]
        assignments = assignment_obj.search(
            [
                ("session_id", "in", self.ids),
                ("teacher_id.active", "=", True),
            ],
            order="session_id, sequence NULLS LAST, id",
        )

        # Take the first reservation per session (already stably ordered)
        first_by_session = {}
        for assignment in assignments:
            session_id = assignment.session_id.id
            if session_id not in first_by_session:
                first_by_session[session_id] = assignment

        for session in self:
            assignment = first_by_session.get(session.id)
            if assignment and assignment.teacher_id:
                session.primary_teacher_id = assignment.teacher_id
            else:
                session.primary_teacher_id = False

    # -- Invitation information
    # -------------------------------------------------------------------------

    invitation_ids = fields.One2many(
        string="Invitation",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="List of attendees for the session",
        comodel_name="academy.training.session.invitation",
        inverse_name="session_id",
        domain=[],
        context={},
        auto_join=False,
        tracking=True,
        copy=False,
    )

    invitation_count = fields.Integer(
        string="Invitation count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions to which the student has been invited",
        compute="_compute_invitation_count",
        search="_search_invitation_count",
        store=False,
    )

    @api.depends("invitation_ids")
    def _compute_invitation_count(self):
        counts = one2many_count(self, "invitation_ids")

        for record in self:
            record.invitation_count = counts.get(record.id, 0)

    @api.model
    def _search_invitation_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "invitation_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    invitation_str = fields.Char(
        string="Invitation summary",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Included / total invitations for this session.",
        compute="_compute_invitation_str",
        store=False,
    )

    @api.depends("invitation_ids", "invitation_ids.included")
    def _compute_invitation_str(self):
        counts = one2many_count(self, "invitation_ids")

        counts = one2many_count(self, "invitation_ids")
        included_counts = one2many_count(
            self, "invitation_ids", [("included", "!=", True)]
        )

        for record in self:
            if not record.id:
                record.invitation_str = "0 / 0"
                continue

            total = counts.get(record.id, 0)
            included = included_counts.get(record.id, 0)
            record.invitation_str = f"{included} / {total}"

    # -- Enrolment information
    # -------------------------------------------------------------------------

    enrolment_ids = fields.Many2manyView(
        string="Enrolments",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Enrolments linked to this session via invitations.",
        comodel_name="academy.training.action.enrolment",
        relation="academy_training_session_invitation",
        column1="session_id",
        column2="enrolment_id",
        domain=[],
        context={},
    )

    student_ids = fields.Many2manyView(
        string="Students",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Students linked to this session via invitations.",
        comodel_name="academy.student",
        relation="academy_training_session_invitation",
        column1="session_id",
        column2="student_id",
        domain=[],
        context={},
    )

    # -- Date interval information
    # -------------------------------------------------------------------------

    date_start = fields.Datetime(
        string="Beginning",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.now_o_clock(round_up=True),
        help="Date/time of session start",
        tracking=True,
    )

    @api.onchange("date_start")
    def _onchange_date_start(self):
        self._compute_date_delay()

    date_stop = fields.Datetime(
        string="Ending",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.now_o_clock(offset_hours=1, round_up=True),
        help="Date/time of session end",
        tracking=True,
    )

    @api.onchange("date_stop")
    def _onchange_date_stop(self):
        self._compute_date_delay()

    date_delay = fields.Float(
        string="Duration",
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Time length of the training session",
        store=True,
        compute="_compute_date_delay",
        aggregator="sum",
    )

    @api.depends("date_start", "date_stop")
    def _compute_date_delay(self):
        for record in self:
            delay = record._time_interval(record.date_start, record.date_stop)
            record.date_delay = delay

    @api.onchange("date_delay")
    def _onchange_duration(self):
        for record in self:
            if record._origin.date_delay != record.date_delay:
                span = record.date_delay * 3600.0
                record.date_stop = record.date_start + timedelta(seconds=span)

    interval_str = fields.Char(
        string="Interval",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Display session time interval",
        size=24,
        translate=False,
        compute="_compute_interval_str",
        search="_search_interval_str",
    )

    @api.depends("date_start", "date_stop")
    def _compute_interval_str(self):
        for record in self:
            second = record.date_start.second or record.date_stop.second
            tformat = "%H:%M:%S" if second else "%H:%M"

            left = record.date_start.strftime(tformat)
            right = record.date_stop.strftime(tformat)

            record.interval_str = "{} - {}".format(left, right)

    @api.model
    def _search_interval_str(self, operator, value):
        """
        Translate period query into an overlap domain on
        (date_start, date_stop).

        Grammar (case-insensitive):
          - day[+N|-N|:D]     → D=1..31 in current month
          - week[+N|-N|:W]    → ISO week W in current year (Mon–Sun)
          - month[+N|-N|:M]   → month M in current year (1..12)
          - year[+N|-N|:YYYY] → absolute year

        Returned domain selects records whose interval overlaps the
        computed [start, end) window:
            (date_start < end) AND (date_stop >= start)

        Unsupported/empty values return a false domain.
        """
        if not value or not isinstance(value, str):
            return FALSE_DOMAIN

        unit, value_num, compute = self._search_interval_split_value(value)
        if compute == "absolute":
            start = self._search_interval_absolute_start(unit, value_num)
        elif compute == "relative":
            start = self._search_interval_relative_start(unit, value_num)
        else:
            return FALSE_DOMAIN

        if not start:
            return FALSE_DOMAIN

        end = self._search_interval_stop(unit, start)
        if not end:
            return FALSE_DOMAIN

        start_dt = datetime.combine(start, time.min)
        end_dt = datetime.combine(end, time.min)

        domain = [
            "&",
            ("date_start", "<", end_dt),
            ("date_stop", ">=", start_dt),
        ]

        return domain

    # -- Business fields
    # -------------------------------------------------------------------------

    lang = fields.Char(
        string="Language",
        required=True,
        readonly=True,
        index=False,
        help=False,
        size=255,
        translate=False,
        compute="_compute_lang",
        store=False,
    )

    @api.depends_context("uid")
    @api.depends("primary_teacher_id")
    def _compute_lang(self):
        """Gets the language used by the current user and sets it as `lang`
        field value
        """

        user_id = self.env["res.users"].browse(self.env.uid)

        for record in self:
            record.lang = user_id.lang

    # -- Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            "check_training_task",
            """
            CHECK(
                (program_type <> \'training\') OR
                (
                    training_action_id IS NOT NULL
                    AND action_line_id IS NOT NULL
                )
            )
            """,
            "Teaching sessions must be linked to a program unit",
        ),
        (
            "check_non_training_task",
            """
                CHECK(
                    (program_type <> \'support\') OR
                    (
                        action_line_id IS NULL
                    )
                )
            """,
            "Non-teaching sessions should not be linked to an program unit",
        ),
        (
            "unique_training_action_id",
            """EXCLUDE USING gist (
                training_action_id gist_int4_ops WITH =,
                tsrange ( date_start, date_stop ) WITH &&
            ) WHERE (validate AND allow_overlap IS NOT TRUE);
            -- Requires btree_gist""",
            "This event overlaps with another of the same training action",
        ),
        (
            "positive_interval",
            "CHECK(date_start < date_stop)",
            "Session cannot end before starting",
        ),
    ]

    @api.constrains("trainint_action_id", "program_type")
    def _check_trainint_action_id(self):
        err_1 = _(
            "Selected training element ('{}') doesn't match the chosen "
            "program type ('{}')."
        )
        err_2 = _(
            "Chosen training group ('{}') belongs to a training action ('{}') "
            "that is not configured to be scheduled by groups."
        )
        err_3 = _(
            "Chosen training action ('{}') is configured to be scheduled by "
            "groups."
        )

        for record in self:
            action = record.training_action_id
            if not action:
                continue

            if action.program_type != record.program_type:
                raise ValidationError(
                    err_1.format(action.display_name, record.program_type)
                )

            is_child = bool(action.parent_id)
            if is_child and not action.parent_id.groupwise_schedule:
                raise ValidationError(err_2.format(action.display_name))
            if not is_child and action.groupwise_schedule:
                raise ValidationError(err_3.format(action.display_name))

    @api.constrains("training_action_id", "action_line_id")
    def _check_training_action_id(self):
        pattern = _(
            'Selected training action line ("{}") must belong to the selected '
            'training action ("{}").'
        )

        for record in self:
            action, line = record.training_action_id, record.action_line_id
            if not action or not line:
                continue
            if line.training_action_id != action:
                raise ValidationError(
                    pattern.format(line.display_name, action.display_name)
                )

    # -- Overriden methods
    # -------------------------------------------------------------------------

    @api.depends(
        "date_start",
        "date_stop",
        "training_action_id",
        "training_action_id.name",
    )
    @api.depends_context(
        "lang", "name_get_session_interval", "default_training_action_id"
    )
    def _compute_display_name(self):
        for record in self:
            if self.env.context.get("name_get_session_interval", False):
                if record.date_start and record.date_stop:
                    dt_start = fields.Datetime.context_timestamp(
                        record, record.date_start
                    )
                    dt_stop = fields.Datetime.context_timestamp(
                        record, record.date_stop
                    )
                    date_base = dt_start.strftime("%d-%m-%Y")
                    time_start = dt_start.strftime("%H:%M")
                    time_stop = dt_stop.strftime("%H:%M")
                    name = f"{date_base} ({time_start} - {time_stop})"
                else:
                    name = self.env._("New session")

            elif self.env.context.get("default_training_action_id", False):
                if record.action_line_id:
                    name = record.action_line_id.name
                else:
                    name = self.env._("New session")
            else:
                if record.training_action_id:
                    name = record.training_action_id.name
                else:
                    name = self.env._("New session")

            record.display_name = name

    @api.model_create_multi
    def create(self, values_list):
        tracking_disable_ctx = self.env.context.copy()
        tracking_disable_ctx.update({"tracking_disable": True})

        result = self.browse()

        for values in values_list:
            self_ctx = self.with_context(tracking_disable_ctx)
            with self.env.cr.savepoint():
                self_ctx._adjust_existing_facility_reservations(values)

            _super = super(AcademyTrainingSession, self)
            result |= _super.create(values)

            if "invitation_ids" not in values:
                result.invite_all()

            if "reservation_ids" in values:
                reservation_values = {
                    "date_start": result.date_start,
                    "date_stop": result.date_stop,
                    "name": result.training_action_id.name,
                    "description": result.action_line_id.name,
                }

                result_ctx = result.with_context(tracking_disable_ctx)
                result_ctx.reservation_ids.write(reservation_values)

        return result

    def write(self, values):
        tracking_disable_ctx = self.env.context.copy()
        tracking_disable_ctx.update({"tracking_disable": True})
        self_ctx = self.with_context(tracking_disable_ctx)

        self._adjust_existing_facility_reservations(values)

        if "action_line_id" in values and "invitation_ids" not in values:
            values["invitation_ids"] = None

        _super = super(AcademyTrainingSession, self)
        result = _super.write(values)

        if "action_line_id" in values and "invitation_ids" not in values:
            self.invite_all()

        if self.reservation_ids:
            reservation_values = {}

            if "date_start" in values:
                reservation_values["date_start"] = values.get("date_start")
            if "date_stop" in values:
                reservation_values["date_stop"] = values.get("date_stop")

            if reservation_values:
                ctx = self.env.context.copy()
                ctx.update(
                    {
                        "active_model": self._name,
                        "active_ids": self.mapped("id"),
                        "tracking_disable": True,
                    }
                )
                self_ctx.reservation_ids.write(reservation_values)

        # self._update_session_followers()

        return result

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()

        default = dict(default or {})

        ctx = dict(self.env.context, tracking_disable=True)
        parent = super(AcademyTrainingSession, self.with_context(ctx))

        if "date_start" not in default:
            date_start = self.date_start + timedelta(days=7)
            default["date_start"] = date_start.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date_start = fields.Datetime.from_string(default["date_start"])

        if "date_stop" not in default:
            date_stop = self.date_stop + timedelta(days=7)
            default["date_stop"] = date_stop.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date_stop = fields.Datetime.from_string(default["date_stop"])

        default["date_delay"] = self._time_interval(date_start, date_stop)

        if "state" not in default:
            default["state"] = "draft"

        if "invitation_ids" not in default:
            default["invitation_ids"] = []
            for inv in self.invitation_ids:
                values = {
                    "enrolment_id": inv.enrolment_id.id,
                    "student_id": inv.student_id.id,
                    "present": False,
                }
                m2m_op = (0, 0, values)
                default["invitation_ids"].append(m2m_op)

        if "teacher_assignment_ids" not in default:
            default["teacher_assignment_ids"] = []
            for ta in self.teacher_assignment_ids:
                values = {
                    "teacher_id": ta.teacher_id.id,
                    "sequence": ta.sequence,
                }
                m2m_op = (0, 0, values)
                default["teacher_assignment_ids"].append(m2m_op)

        if "reservation_ids" not in default:
            default["reservation_ids"] = []
            for rv in self.reservation_ids:
                facility = rv.facility_id
                values = {
                    "facility_id": facility.id,
                    "sequence": rv.sequence,
                    "date_start": default["date_start"],
                    "date_stop": default["date_stop"],
                    "state": rv.state,
                }
                m2m_op = (0, 0, values)
                default["reservation_ids"].append(m2m_op)

        return parent.copy(default=default)

    # -- Public methods
    # -------------------------------------------------------------------------

    @staticmethod
    def now_o_clock(offset_hours=0, round_up=False):
        present = fields.datetime.now()
        oclock = present.replace(minute=0, second=0, microsecond=0)

        if round_up and (oclock < present):  # almost always
            oclock += timedelta(hours=1)

        return oclock + timedelta(hours=offset_hours)

    def date_delay_str(self, span=None):
        self.ensure_one()

        if span is None:
            span = self.date_delay or 0

        hours = int(span)
        pattern = "{h:02d} h"

        span = span % 1
        minutes = int(span * 60)
        if minutes:
            pattern += " {m:02d}'"

        span = (span * 60) % 1
        seconds = int(span * 60)
        if seconds:
            pattern += ' {s:02d}"'

        return pattern.format(h=hours, m=minutes, s=seconds)

    def get_tz(self):
        """Retrieve session timezone if available.

        The timezone can correspond, in order of priority, to:
        1) The complex pertaining to the main classroom.
        2) The company associated with the session.
        3) The administrator of the session.
        4) Default to Coordinated Universal Time (UTC).

        Returns:
            pytz.timezone: Timezone instance or UTC if not found.
        """

        self.ensure_one()

        tz = self.mapped("primary_facility_id.complex_id.partner_id.tz")
        if not tz:
            tz = self.mapped("company_id.partner_id.tz")
        if not tz:
            tz = self.mapped("manager_id.partner_id.tz")

        tz = tz and tz[0] or "UTC"  # First value in list or 'UTC'

        return pytz.timezone(tz)

    @staticmethod
    def localized_dt(value, tz, show_tz=False):
        """
        Converts and localizes a given datetime or date value to the specified
        timezone.

        This method will be used by ``_notify_prepare_template_context`` to
        adjust the display of dates and times in email notifications based on
        the session's timezone.

        Args:
            value (date | datetime): Date or datetime value to be localized.
            tz (str): Timezone identifier string, e.g., 'Europe/Madrid'.
            show_tz (bool, optional): If set to True, appends the timezone name
                                      to the resulting string representation.

        Returns:
            str: Localized string representation of the given date or datetime
                 value.
        """

        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, date):
            dt = datetime.combine(value, time.min)
        else:
            return value

        dt = pytz.utc.localize(dt)
        dt = dt.astimezone(tz)

        if isinstance(value, datetime):
            result = dt.strftime("%c")
        else:
            result = dt.date().strftime("%x")

        if show_tz:
            result = "{} ({})".format(result, _(tz.zone))

        return result

    def view_timesheets(self):
        action_xid = (
            "academy_timesheets."
            "action_academy_training_session_timesheet_act_window"
        )
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))

        if self:
            domain = [("training_session_id", "in", self.mapped("id"))]
        else:
            domain = TRUE_DOMAIN

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": action.res_model,
            "target": action.target,
            "name": action.name,
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized

    def view_invitations(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_invitation_act_window"
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({"default_session_id": self.id})

        domain = [("session_id", "=", self.id)]

        view_modes = action.view_mode.split(",")
        view_modes = [mode for mode in view_modes if mode != "list"]
        view_modes.insert(0, "list")

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.training.session.invitation",
            "target": "current",
            "name": self.env._("Invitations"),
            "view_mode": ",".join(view_modes),
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized

    def view_reservations(self):
        self.ensure_one()

        action_xid = "facility_management.action_reservations_act_window"
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update(
            {
                "default_session_id": self.id,
                "default_date_start": self.date_start,
                "default_date_stop": self.date_stop,
            }
        )

        domain = [("session_id", "=", self.id)]

        view_modes = action.view_mode.split(",")
        view_modes = [item for item in view_modes if item != "calendar"]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "facility.reservation",
            "target": "current",
            "name": self.env._("Reservations"),
            "view_mode": ",".join(view_modes),
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized

    def view_teachers(self):
        self.ensure_one()

        action_xid = "academy_base.action_teacher_act_window"
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({"default_session_id": self.id})
        ctx.update({"create": False, "delete": False, "edit": False})

        domain = [("session_ids.id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": action.res_model,
            "target": "current",
            "name": self.env._("Teachers"),
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized

    def invite_all(self):
        enrol_obj = self.env["academy.training.action.enrolment"]
        invitation_obj = self.env["academy.training.session.invitation"]

        for record in self:
            invitation_ops = []

            date_start = record.date_start.strftime(DATE_FORMAT)
            date_stop = record.date_stop.strftime(DATE_FORMAT)

            enrol_domain = [
                "&",
                "&",
                "&",
                ("training_action_id", "=", record.training_action_id.id),
                ("action_line_ids", "=", record.action_line_id.id),
                ("register", "<=", date_start),
                "|",
                ("deregister", "=", False),
                ("deregister", ">=", date_stop),
            ]

            enrol_set = enrol_obj.search(enrol_domain)

            for enrol in enrol_set:
                domain = [
                    (
                        "session_id",
                        "=",
                        record.id,
                    ),
                    ("enrolment_id", "=", enrol.id),
                ]
                invitation = invitation_obj.search(domain, limit=1)

                if invitation:
                    o2m_op = (1, invitation.id)
                else:
                    o2m_op = (
                        0,
                        0,
                        {"session_id": record.id, "enrolment_id": enrol.id},
                    )

                invitation_ops.append(o2m_op)

            record.write({"invitation_ids": invitation_ops})

    def toggle_followers(self):
        path = "teacher_assignment_ids.teacher_id.res_users_id." "partner_id"

        current_partner = self.env.user.partner_id

        for record in self:
            suscribe_set = record.mapped(path) + current_partner

            keep_set = (
                suscribe_set
                + record.owner_id.partner_id
                + record.subrogate_id.partner_id
            )

            unsuscribe_set = self.message_partner_ids.filtered(
                lambda r: r not in keep_set
            )

            if suscribe_set:
                partner_ids = suscribe_set.mapped("id")
                record.message_subscribe(partner_ids=partner_ids)

            if unsuscribe_set:
                partner_ids = unsuscribe_set.mapped("id")
                self.message_unsubscribe(partner_ids=partner_ids)

    def send_by_mail(self):
        """ """
        context = self.env.context.copy()
        context.update({"include_schedule_url": True})

        tpl_xid = "academy_timesheets.mail_template_training_session_details"
        email_template = self.env.ref(tpl_xid).with_context(context)

        send_mail = email_template.send_mail

        for record in self:
            teacher_set = self.mapped("teacher_assignment_ids.teacher_id")
            for teacher in teacher_set:
                address = "{} <{}>".format(teacher.name, teacher.email)
                evalues = {"email_to": address}
                send_mail(record.id, email_values=evalues, force_send=True)

    def copy_all(self, default=None):
        target_set = self.env["academy.training.session"]
        for record in self:
            target_set += record.copy(default)

        return target_set

    def toogle_state(self, force_to=None):
        for record in self:
            if force_to in ("draft", "ready"):
                record.state = force_to
            elif record.state == "draft":
                record.state = "ready"
            else:  # Current state is ready
                record.state = "draft"

    @api.model
    def view_my_schedule(self):
        user_id = self.env.context.get("uid", False)

        domain = [("res_users_id", "=", user_id)]
        teacher_obj = self.env["academy.teacher"]
        teacher = teacher_obj.search(domain, limit=1)

        if not teacher:
            msg = self.env._("You currently do not have teaching activity.")
            raise UserError(msg)

        act_window = teacher.view_sessions(definitive=False)
        act_window.update(views=self._compute_view_mapping())

        return act_window

    def download_my_schedule(self):
        user_id = self.env.context.get("uid", False)

        domain = [("res_users_id", "=", user_id)]
        teacher_obj = self.env["academy.teacher"]
        teacher = teacher_obj.search(domain, limit=1)

        if not teacher:
            msg = self.env._("You currently do not have teaching activity.")
            raise UserError(msg)

        return {
            "name": self.env._("My schedule"),
            "type": "ir.actions.act_url",
            "url": "/academy-timesheets/teacher/schedule",
            "target": "blank",
        }

    @api.model
    def wizard_search_for_available_facilities(self):
        return {
            "name": "Search for available facilities ",
            "res_model": "ir.actions.act_url",
            "type": "ir.actions.act_url",
            "target": "wizard_facilities",
            "url": "/academy_timesheets/redirect/facilities",
        }

    @api.model
    def wizard_search_for_available_teachers(self):
        return {
            "name": "Search for available facilities ",
            "res_model": "ir.actions.act_url",
            "type": "ir.actions.act_url",
            "target": "wizard_teachers",
            "url": "/academy_timesheets/redirect/teachers",
        }

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def _track_subtype(self, init_values):
        self.ensure_one()

        fields = [
            "date_start",
            "date_stop",
            "active",
            "state",
            "training_action_id",
            "action_line_id",
            "primary_teacher_id",
            "primary_facility_id",
            "teacher_assignment_ids",
            "reservation_ids",
        ]

        xid = "academy_timesheets.{}"
        result = False

        if self.state != "draft" and any(key in fields for key in init_values):
            xid = xid.format("academy_timesheets_training_session_changed")
            result = self.env.ref(xid)
        elif init_values.get("state", False) == "ready":
            xid = xid.format("academy_timesheets_training_session_draft")
            result = self.env.ref(xid)
        else:
            _super = super(AcademyTrainingSession, self)
            result = _super._track_subtype(init_values)

        return result

    def _get_session_timezone(self, message):
        """
        Retrieve session timezone if available. It will be used to communicate
        time changes to the teachers involved in the session. See: ``get_tz``

        Args:
            message (mail.message): The message object.

        Returns:
            pytz.timezone: Timezone instance or UTC if not found.
        """

        try:
            session = self.env[message.model].browse(message.res_id)
            return session.get_tz() if session else False

        except Exception:
            msg = self.env._("Session with id #{} not found")
            _logger.error(msg.format(message.res_id))
            return None

    @staticmethod
    def _time_interval(start, stop):
        if start and stop:
            difference = stop - start
            value = max(difference.total_seconds(), 0)
        else:
            value = 0

        return value / 3600.0

    @api.model
    def _read_help_to_fill_configuration(self):
        config = self.env["ir.config_parameter"].sudo()
        help_to_fill = config.get_param(
            "academy_timesheets.help_to_fill", False
        )
        wait_to_fill = config.get_param(
            "academy_timesheets.wait_to_fill", "0.0"
        )

        return help_to_fill, safe_eval(wait_to_fill)

    @api.model
    def _get_last_session(self, teacher_id, seconds):
        now = fields.Datetime.now() - timedelta(seconds=seconds)
        tformat = "%Y-%m-%d %H:%M:%S"

        domain = [
            "&",
            ("primary_teacher_id", "=", teacher_id),
            ("create_date", ">=", now.strftime(tformat)),
        ]
        session_obj = self.env["academy.training.session"]
        return session_obj.search(domain, order="create_date DESC", limit=1)

    @staticmethod
    def _serialize_session(session):
        tformat = "%Y-%m-%d %H:%M:%S"

        values = {
            "state": session.state,
            "description": session.description,
            "program_type": session.program_type,
            "validate": session.validate,
            "training_action_id": session.training_action_id.id,
            "action_line_id": session.action_line_id.id,
            "teacher_assignment_ids": [(5, 0, 0)],
            "reservation_ids": [(5, 0, 0)],
            "invitation_ids": [(5, 0, 0)],
        }

        for assign in session.teacher_assignment_ids:
            m2m_op = (
                0,
                0,
                {
                    "teacher_id": assign.teacher_id.id,
                    "sequence": assign.sequence,
                },
            )
            values["teacher_assignment_ids"].append(m2m_op)

        for reservation in session.reservation_ids:
            m2m_op = (
                0,
                0,
                {
                    "date_start": reservation.date_start.strftime(tformat),
                    "date_stop": reservation.date_stop.strftime(tformat),
                    "sequence": reservation.sequence,
                    "facility_id": reservation.facility_id.id,
                    "owner_id": reservation.owner_id.id,
                    "subrogate_id": reservation.subrogate_id.id,
                    "state": reservation.state,
                },
            )
            values["reservation_ids"].append(m2m_op)

        for invitation in session.invitation_ids:
            m2m_op = (
                0,
                0,
                {
                    "session_id": invitation.session_id.id,
                    "enrolment_id": invitation.enrolment_id.id,
                    "active": invitation.active,
                },
            )
            values["invitation_ids"].append(m2m_op)

        return values

    # def _update_session_followers(self):
    #     path = ('teacher_assignment_ids.teacher_id.res_users_id.'
    #             'partner_id.id')

    #     for record in self:
    #         partner_ids = record.mapped(path)
    #         if record.state == 'ready':
    #             record.message_subscribe(partner_ids=partner_ids)

    @staticmethod
    def _real_id(record_set, single=False):
        """Return a list with no NewId's of a single no NewId"""

        result = []

        if record_set and single:
            record_set.ensure_one()

        for record in record_set:
            if isinstance(record.id, models.NewId):
                result.append(record._origin.id)
            else:
                result.append(record.id)

        if single:
            result = result[0] if len(result) == 1 else None

        return result

    def _compute_view_mapping(self):
        view_names = [
            "view_academy_training_session_calendar_teacher_readonly",
            "view_academy_training_session_kanban_teacher_readonly",
            "view_academy_training_session_tree_teacher_readonly",
            "view_academy_training_session_form_teacher_readonly",
        ]

        view_mapping = []
        for view_name in view_names:
            xid = "academy_timesheets.{}".format(view_name)
            view = self.env.ref(xid)
            pair = (view.id, view.type)
            view_mapping.append(pair)

        return view_mapping

    # -------------------------------------------------------------------------
    # Method: _adjust_existing_facility_reservations
    # -------------------------------------------------------------------------

    def _adjust_existing_facility_reservations(self, values):
        reservation_set = self.env["facility.reservation"]

        for record in self:
            record_reservation_set = (
                record._search_for_overlapping_reservations(values)
            )

            date_start, date_stop = record._compute_new_datetimes(values)

            for reservation in record_reservation_set:
                if record._is_entirely_encompasses(
                    reservation, date_start, date_stop
                ):
                    record._entirely_encompasses(reservation)

                elif record._is_starts_before(
                    reservation, date_start, date_stop
                ):
                    record._starts_before(reservation, date_stop)
                    reservation_set |= reservation

                elif record._is_ends_after(reservation, date_start, date_stop):
                    record._ends_after(reservation, date_start)
                    reservation_set |= reservation

                elif record._is_partially_encompasses(
                    reservation, date_start, date_stop
                ):
                    record._partially_encompasses(
                        reservation, date_start, date_stop
                    )
                    reservation_set |= reservation

        return reservation_set

    @staticmethod
    def _is_entirely_encompasses(reservation, date_start, date_stop):
        return (
            date_start <= reservation.date_start
            and date_stop >= reservation.date_stop
        )

    @staticmethod
    def _is_starts_before(reservation, date_start, date_stop):
        return (
            date_start <= reservation.date_start
            and date_stop < reservation.date_stop
        )

    @staticmethod
    def _is_ends_after(reservation, date_start, date_stop):
        return (
            date_start > reservation.date_start
            and date_stop >= reservation.date_stop
        )

    @staticmethod
    def _is_partially_encompasses(reservation, date_start, date_stop):
        return (
            date_start > reservation.date_start
            and date_stop < reservation.date_stop
        )

    @staticmethod
    def _entirely_encompasses(reservation):
        """╔═══╗→
        ║   ║───┐
        ║ S ║ R │x  Reservation will be removed
        ╚═══╝───┘
        """
        reservation.unlink()

    @staticmethod
    def _starts_before(reservation, date_stop):
        """╔═══╗
        ║ S ║───┐↓  Reservation will be reduced towards the end date
        ╚═══╝ R │
         →  └───┘
        """
        if reservation.date_stop > date_stop:
            date_start = fields.Datetime.to_string(date_stop)
            reservation.write({"date_start": date_start, "scheduler_id": None})
        else:
            reservation.unlink()

    @staticmethod
    def _ends_after(reservation, date_start):
        """→  ┌───┐
        ╔═══╗ R │
        ║ S ║───┘↑  Reservation will be reduced towards the start date
        ╚═══╝
        """
        if reservation.date_start < date_start:
            date_stop = fields.Datetime.to_string(date_start)
            reservation.write({"date_stop": date_stop, "scheduler_id": None})
        else:
            reservation.unlink()

    def _partially_encompasses(self, reservation, date_start, date_stop):
        """┌───┐   ┌─¹─┐
        ╔═══╗   │↑  └───┘ Old reservation
        ║ S ║ R │
        ╚═══╝   │   ┌───┐
        →   └───┘   └─²─┘ New empty reservation
        """
        top_date_stop = fields.Datetime.to_string(reservation.date_stop)

        reservation.write(
            {
                "date_stop": fields.Datetime.to_string(date_start),
                "scheduler_id": None,
            }
        )

        reservation_obj = self.env["facility.reservation"]
        values = {
            "date_start": fields.Datetime.to_string(date_stop),
            "date_stop": top_date_stop,
            "training_action_id": self.training_action_id.id,
            "facility_id": reservation.facility_id.id,
            "scheduler_id": None,
        }
        reservation_obj.create(values)

    # -------------------------------------------------------------------------
    # Method: _search_for_overlapping_reservations
    # -------------------------------------------------------------------------

    def _append_facility_domain(self, domains, values):
        facility_ids = self._catch_all_facilities(values)

        if facility_ids:
            same_facility_domain = [("facility_id", "in", facility_ids)]
            domains.append(same_facility_domain)

    @staticmethod
    def _append_without_session_domain(domains):
        without_session_domain = [("session_id", "=", False)]
        domains.append(without_session_domain)

    def _append_training_action_domain(self, domains, values):
        training_action_id = values.get("training_action_id", False)
        if not training_action_id:
            training_action_id = self.training_action_id.id

        if training_action_id:
            same_training_action_domain = [
                ("training_action_id", "=", training_action_id)
            ]
            domains.append(same_training_action_domain)
        else:
            message = "A training action has not been found as expected"
            raise MissingError(message)

    def _append_overlapping_domain(self, domains, values):
        date_start, date_stop = self._compute_new_datetimes(
            values, as_str=True
        )

        if date_start and date_stop:
            overlapped_domain = [
                "&",
                ("date_start", "<", date_stop),
                ("date_stop", ">", date_start),
            ]
            domains.append(overlapped_domain)
        else:
            message = (
                "The date range for the training session could not be "
                "determined"
            )
            raise MissingError(message)

    @staticmethod
    def _append_confirmed_domain(domains):
        state_confirmed_domain = [("state", "=", "confirmed")]
        domains.append(state_confirmed_domain)

    def _search_for_overlapping_reservations(self, values):
        reservation_obj = self.env["facility.reservation"]
        domains = []

        self._append_facility_domain(domains, values)
        if not domains:
            return reservation_obj

        self._append_without_session_domain(domains)
        self._append_training_action_domain(domains, values)
        self._append_overlapping_domain(domains, values)
        self._append_confirmed_domain(domains)

        domain = AND(domains)
        reservation_set = reservation_obj.search(domain)

        return reservation_set

    def _compute_new_datetimes(self, values, as_str=False):
        date_start = values.get("date_start", False) or self.date_start
        date_stop = values.get("date_stop", False) or self.date_stop

        if as_str:
            if isinstance(date_start, datetime):
                date_start = fields.Datetime.to_string(date_start)

            if isinstance(date_stop, datetime):
                date_stop = fields.Datetime.to_string(date_stop)
        else:
            if isinstance(date_start, str):
                date_start = fields.Datetime.from_string(date_start)

            if isinstance(date_stop, str):
                date_stop = fields.Datetime.from_string(date_stop)

        return date_start, date_stop

    # -------------------------------------------------------------------------
    # Method: _catch_all_facilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _catch_stock_method(stock, perform):
        if perform == "add":
            return getattr(stock, "update")
        elif perform == "remove":
            return getattr(stock, "difference_update")
        else:
            return None

    @staticmethod
    def _catch_from_values(stock, values):
        if values and isinstance(values, dict) and "facility_id" in values:
            facility_id = values.get("facility_id", False)
            if facility_id:
                stock.add(facility_id)
                return [facility_id]

        return []

    @api.model
    def _catch_from_ids(self, stock, ids=None, perform="add", clear=False):
        if clear:
            stock.clear()

        if ids and isinstance(ids, (tuple, list, int)):
            reservation_obj = self.env["facility.reservation"]
            reservation_set = reservation_obj.browse(ids)

            facility_ids = reservation_set.facility_id.ids
            if facility_ids:
                method = self._catch_stock_method(stock, perform)
                if method:
                    method(facility_ids)

                return facility_ids

        return []

    def _catch_all_facilities(self, values):
        """
        (0, 0,  { values }) link to a new record
        (1, ID, { values }) update the linked record with id = ID
        (2, ID)             remove and delete the linked record
        (3, ID)             cut the link to the linked record with id = ID
        (4, ID)             link to existing record with id = ID
        (5)                 unlink all (like using (3,ID)
        (6, 0, [IDs])       replace the list of linked IDs
        """

        facility_stock = set(self.mapped("reservation_ids.facility_id.id"))

        if values and "reservation_ids" in values:
            m2m_ops = values.get("reservation_ids")

            for m2m_op in m2m_ops:
                if not (isinstance(m2m_op, (tuple, list)) and len(m2m_op) > 1):
                    continue

                if m2m_op[0] == 0 and len(m2m_op) > 2:
                    self._catch_from_values(facility_stock, m2m_op[2])

                elif m2m_op[0] == 1:
                    new_facility_ids = self._catch_from_values(
                        facility_stock, m2m_op[2]
                    )
                    old_facility_ids = self._catch_from_ids(
                        facility_stock, m2m_op[1]
                    )

                    if (
                        old_facility_ids
                        and new_facility_ids
                        and old_facility_ids[0] != new_facility_ids[0]
                    ):
                        facility_stock.difference_update(old_facility_ids)
                        facility_stock.update(new_facility_ids)

                elif m2m_op[0] in (2, 3):
                    self._catch_from_ids(
                        facility_stock, m2m_op[1], perform="remove"
                    )

                elif m2m_op[0] == 4:
                    self._catch_from_ids(facility_stock, m2m_op[1])

                elif m2m_op[0] == 5:
                    self._catch_from_ids(facility_stock, clear=True)

                elif m2m_op[0] == 6:
                    self._catch_from_ids(facility_stock, m2m_op[2], clear=True)

        return list(facility_stock)

    # -------------------------------------------------------------------------
    # Auxiliary methods: _search_interval_str
    # -------------------------------------------------------------------------

    @staticmethod
    def _search_interval_split_value(value):
        unit, num, compute = None, None, None
        if not value or not isinstance(value, str):
            return unit, num, compute

        normalized_value = value.strip().lower()
        regex_result = _INTERVAL_RE.match(normalized_value)
        if not regex_result:
            return unit, num, compute

        unit, absolute_raw, relative_raw = regex_result.groups()
        if absolute_raw is not None:
            absolute = int(absolute_raw)
            if absolute > 0:
                num = absolute
                compute = "absolute"
        elif relative_raw is not None:
            # Accept +0 / -0 as valid relative offset
            num = int(relative_raw)
            compute = "relative"
        else:
            # Unit without value then use: relative +0 offset
            num = 0
            compute = "relative"

        return unit, num, compute

    def _search_interval_absolute_start(self, unit, value_num):
        start = None
        date_base = fields.Date.context_today(self)  # date

        if unit == "day":
            _, mdays = calendar.monthrange(date_base.year, date_base.month)
            if 1 <= value_num <= mdays:
                start = date(date_base.year, date_base.month, value_num)
        elif unit == "week":
            try:
                start = date.fromisocalendar(date_base.year, value_num, 1)
            except ValueError:
                pass
        elif unit == "month":
            if 1 <= value_num <= 12:
                start = date(date_base.year, value_num, 1)
        elif unit == "year":
            start = date(value_num, 1, 1)

        return start

    def _search_interval_relative_start(self, unit, value_num):
        start = None
        date_base = fields.Date.context_today(self)  # date

        if unit == "day":
            start = date_base + timedelta(days=value_num)
        elif unit == "week":
            monday = date_base - timedelta(days=date_base.weekday())
            start = monday + timedelta(days=7 * value_num)
        elif unit == "month":
            first = date_base.replace(day=1)
            start = first + relativedelta(months=value_num)
        elif unit == "year":
            new_year = date_base.year + value_num
            start = date(new_year, 1, 1)

        return start

    def _search_interval_stop(self, unit, start):
        end = None

        if unit == "day":
            end = start + timedelta(days=1)
        elif unit == "week":
            end = start + timedelta(days=7)
        elif unit == "month":
            end = start + relativedelta(months=1)
        elif unit == "year":
            end = date(start.year + 1, 1, 1)

        return end
