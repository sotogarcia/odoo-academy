# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.training.action Odoo model which stores
all training action attributes and behavior.
"""


from odoo.tools.translate import _, _lt
from odoo.tools.misc import format_date

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import ARCHIVED_DOMAIN, INCLUDE_ARCHIVED_DOMAIN
from ..utils.datetime_utils import local_midnight_as_utc
from ..utils.helpers import sanitize_code, default_code

from logging import getLogger
from pytz import utc
from uuid import uuid4
from psycopg2 import Error as PsqlError
from enum import IntFlag, auto
from datetime import datetime, date, time, timedelta

CODE_SEQUENCE = "academy.training.action.sequence"

_logger = getLogger(__name__)


class SyncMode(IntFlag):
    NONE = 0
    CREATE = auto()
    READ = auto()  # will be ignored
    UPDATE = auto()
    DELETE = auto()
    UPSERT = UPDATE | CREATE
    ALL = UPDATE | CREATE | DELETE


# pylint: disable=locally-disabled, R0903
class AcademyTrainingAction(models.Model):
    """The training actions represent several groups of students for the same
    training program
    """

    MSG_ATA01 = _lt(
        "There are enrolments that are outside the range of " "training action"
    )

    _name = "academy.training.action"
    _description = "Academy training action"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "ownership.mixin",
    ]

    _rec_name = "name"
    order = "name, date_start"
    _rec_names_search = ["name", "code", "training_program_id"]

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
        default=None,
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

    training_group_ids = fields.One2many(
        string="Training groups",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="academy.training.action.group",
        inverse_name="training_action_id",
        domain=[],
        context={},
        auto_join=False,
    )

    training_group_count = fields.Integer(
        string="Training group count",
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=False,
        compute="_compute_training_group_count",
        search="_search_training_group_count",
    )

    @api.depends("training_group_ids")
    def _compute_training_group_count(self):
        counts = one2many_count(self, "training_group_ids")

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

        counts = one2many_count(self.search([]), "training_group_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

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
    )

    training_action_category_id = fields.Many2one(
        string="Training action category",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related training action",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
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
    )

    # -- Training program and its attributes ----------------------------------

    training_program_id = fields.Many2one(
        string="Training program",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Training program will be imparted in this action",
        comodel_name="academy.training.program",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
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
    )

    action_line_count = fields.Integer(
        string="Action line count",
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=False,
        compute="_compute_action_line_count",
        search="_search_training_action_count",
    )

    @api.depends("action_line_ids")
    def _compute_action_line_count(self):
        counts = one2many_count(self, "action_line_ids")

        for record in self:
            record.action_line_count = counts.get(record.id, 0)

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

        counts = one2many_count(self.search([]), "action_line_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    seating = fields.Integer(
        string="Seating",
        required=True,
        readonly=False,
        index=False,
        default=20,
        help="Maximum number of signups allowed",
    )

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

    @api.onchange("seating")
    def _onchange_seating(self):
        self.excess = max(self.seating, self.excess)

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

    # ------------------------------ CONSTRAINS -------------------------------

    _sql_constraints = [
        (
            "unique_action_code",
            'UNIQUE("code")',
            "The given action code already exists",
        ),
        (
            "check_date_order",
            'CHECK("date_stop" IS NULL OR "date_start" < "date_stop")',
            "End date must be greater then date_start date",
        ),
        (
            "users_greater_or_equal_to_zero",
            "CHECK(seating >= 0)",
            "The number of users must be greater than or equal to zero",
        ),
    ]

    @api.constrains("date_start", "date_stop", "training_group_ids")
    def _constrains_groups_inside_action(self):
        group_obj = self.env["academy.training.action.group"]

        error_start = _("Group starts before action start.")
        error_stop = _("Group ends after action stop.")

        infinity = fields.Datetime.to_datetime("9999-12-31 23:59:59")

        for action in self:
            domain = [
                ("training_action_id", "=", action.id),
                ("date_start", "!=", False),
            ]

            action_start = action.date_start
            action_stop = action.date_stop or infinity

            for group in group_obj.search(domain):
                group_start = group.date_start
                group_stop = group.date_stop or infinity

                if action_start and group_start < action_start:
                    raise ValidationError(error_start)
                if group_stop > action_stop:
                    raise ValidationError(error_stop)

    @api.constrains("seating", "excess", "training_group_ids")
    def _constrains_group_capacity(self):
        error_seating = _("Sum of groups 'Seating' exceeds action 'Seating'.")
        error_excess = _("Sum of groups 'Excess' exceeds action 'Excess'.")

        for action in self:
            groups = action.training_group_ids

            seat_sum = sum(groups.mapped("seating")) if groups else 0
            excess_sum = sum(groups.mapped("excess")) if groups else 0

            if seat_sum > action.seating:
                raise ValidationError(error_seating)

            if excess_sum > action.excess:
                raise ValidationError(error_excess)

    # -------------------------- OVERLOADED METHODS ---------------------------

    @api.returns("self", lambda value: value.id)
    def copy(self, defaults=None):
        """Prevents new record of the inherited (_inherits) model will be
        created
        """

        action_obj = self.env[self._name]
        action_set = action_obj.search([], order="id DESC", limit=1)

        defaults = dict(defaults or {})
        # default.update({
        #     'training_program_id': self.training_program_id.id
        # })
        #
        if "code" not in defaults:
            defaults["code"] = uuid4().hex.upper()

        if "name" not in defaults:
            defaults["name"] = "{} - {}".format(self.name, action_set.id + 1)

        rec = super(AcademyTrainingAction, self).copy(defaults)
        return rec

    @api.model
    def _create(self, values):
        """Overridden low-level method '_create' to handle custom PostgreSQL
        exceptions.

        This method handles custom PostgreSQL exceptions, specifically catching
        the exception with code 'ATE01', triggered by a database trigger that
        validates enrolment dates in training actions.

        Args:
            values (dict): The values to create a new record.

        Returns:
            Record: The newly created record.

        Raises:
            ValidationError: If a PostgreSQL error with code 'ATE01' is raised.
        """

        parent = super(AcademyTrainingAction, self)

        try:
            result = parent._create(values)
        except PsqlError as ex:
            if "ATA01" in str(ex.pgcode):
                raise ValidationError(self.MSG_ATA01)
            else:
                raise

        return result

    def _write(self, values):
        """Overridden low-level method '_write' to handle custom PostgreSQL
        exceptions.

        This method handles custom PostgreSQL exceptions, specifically catching
        the exception with code 'ATE01', triggered by a database trigger that
        validates enrolment dates in training actions.

        Args:
            values (dict): The values to update the record.

        Returns:
            Boolean: True if the write operation was successful.

        Raises:
            ValidationError: If a PostgreSQL error with code 'ATE01' is raised.
        """

        parent = super(AcademyTrainingAction, self)

        try:
            result = parent._write(values)
        except PsqlError as ex:
            if "ATA01" in str(ex.pgcode):
                raise ValidationError(self.MSG_ATA01)
            else:
                raise

        return result

    @api.model_create_multi
    def create(self, value_list):
        """Overridden method 'create'"""
        sanitize_code(value_list, "upper")

        parent = super(AcademyTrainingAction, self)
        result = parent.create(value_list)

        to_sync = result.filtered(lambda r: not r.action_line_ids)
        to_sync.synchronize_from_program(mode=SyncMode.ALL, add_optional=True)

        result.update_enrolments()

        return result

    def write(self, values):
        """Overridden method 'write'"""
        sanitize_code(values, "upper")

        parent = super(AcademyTrainingAction, self)
        result = parent.write(values)

        self.update_enrolments()

        return result

    # --------------------------- PUBLIC METHODS ------------------------------

    def view_training_action_groups(self):
        self.ensure_one()

        action_xid = "academy_base.action_training_action_group_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_action_id": self.id})

        domain = [("training_action_id", "=", self.id)]

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

    def view_action_lines(self):
        self.ensure_one()

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
            "name": act_wnd.name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def update_enrolments(self, force=False):
        dtformat = "%Y-%m-%d %H:%M:%S.%f"

        for record in self:
            enrol_set = record.enrolment_ids

            # Enrolment date_start must be great or equal than record date_start
            target_set = enrol_set.filtered(
                lambda r: r.date_start < record.date_start
            )
            target_set.write(
                {"date_start": record.date_start.strftime(dtformat)}
            )

            # Enrolment end must be less or equal than record end
            # NOTE: end date can be null
            if record.date_stop:
                target_set = enrol_set.filtered(
                    lambda r: r.date_stop and r.date_stop > record.date_stop
                )
                target_set.write(
                    {"date_stop": record.date_stop.strftime(dtformat)}
                )

    def session_wizard(self):
        """Launch the Session wizard.
        This wizard has a related window action, this method reads the action,
        updates context using current evironment and sets the wizard training
        action to this action.
        """

        module = "academy_base"
        name = "action_academy_training_session_wizard_act_window"
        act_xid = "{}.{}".format(module, name)

        self.ensure_one()

        # STEP 1: Initialize variables
        action = self.env.ref(act_xid)
        actx = safe_eval(action.context)

        # STEP 2 Update context:
        ctx = dict()
        ctx.update(self.env.context)  # dictionary from environment
        ctx.update(actx)  # add action context

        # STEP 3: Set training action for wizard. This action will be send in
        # context as a default value. If this recordset have not records,
        # any training action will be set
        if self.id:
            ctx.update(dict(default_training_action_id=self.id))

        # STEP 4: Map training action and add computed context
        action_map = {
            "type": action.type,
            "name": action.name,
            "res_model": action.res_model,
            "view_mode": action.view_mode,
            "target": action.target,
            "domain": action.domain,
            "context": ctx,
            "search_view_id": action.search_view_id,
            "help": action.help,
        }

        # STEP 5: Return the action
        return action_map

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
                domain = eval(domain)
            except Exception:
                domain = []

        return domain

    def view_enrolments(self):
        self.ensure_one()

        act_xid = "academy_base.action_training_action_enrolment_act_window"
        action = self.env.ref(act_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({"default_training_action_id": self.id})

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [("training_action_id", "=", self.id)]])

        action_values = {
            "name": "{} {}".format(_("Enroled in"), self.name),
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

    def copy_activity_image(self):
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

    def _synchronize_from_program(self, mode, add_optional=True):
        """
        Synchronize this training action's lines with their program lines.

        The `mode` bitfield controls which operations are performed:
        - UPDATE: update existing action lines from their program line.
        - CREATE: create missing action lines from program lines.
        - DELETE: delete action lines whose program line is not present.

        Args:
            mode (SyncMode | int): Bitfield of SyncMode flags.
            add_optional (bool): If False, skip creating optional program lines.
        """
        self.ensure_one()

        mode = SyncMode(mode) & SyncMode.ALL
        training_action = self
        action_line_obj = self.env["academy.training.action.line"]

        program_lines = training_action.training_program_id.program_line_ids
        program_line_ids = set(program_lines.ids)

        to_update = action_line_obj.browse()
        to_delete = action_line_obj.browse()

        for action_line in self.action_line_ids:
            program_line = action_line.program_line_id
            if not program_line:
                to_delete |= action_line
            elif program_line.id not in program_line_ids:
                to_delete |= action_line
                program_lines -= program_line
            else:
                to_update |= action_line
                program_lines -= program_line

        if to_update and (mode & SyncMode.UPDATE):
            to_update.update_from_program_line()

        if to_delete and (mode & SyncMode.DELETE):
            to_delete.unlink()

        if program_lines and (mode & SyncMode.CREATE):
            if not add_optional:
                program_lines = program_lines.filtered(
                    lambda r: not r.optional
                )

            action_line_obj.create_from_program_line(
                training_action, program_lines
            )

    def synchronize_from_program(
        self, mode: SyncMode = SyncMode.ALL, add_optional: bool = True
    ):
        """
        Synchronize each training action with its program lines.

        Iterates over the current recordset and delegates to
        `_synchronize_from_program` for each record.

        Note: the READ flag is ignored.

        Args:
            mode (SyncMode): Bitfield flags controlling UPDATE/CREATE/DELETE.
            add_optional (bool): If False, skip creating optional lines.
        """
        mode = SyncMode(mode) & SyncMode.ALL

        for record in self:
            record._synchronize_from_program(mode, add_optional)
