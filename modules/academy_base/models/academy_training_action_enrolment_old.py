# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module contains the academy.training.action.enrolment Odoo model which
stores all training action enrolment attributes and behavior.
"""


from odoo import models, fields, api
from odoo.tools.translate import _, _lt
from odoo.exceptions import UserError
from odoo.osv.expression import TERM_OPERATORS_NEGATION
from odoo.exceptions import ValidationError

from odoo.addons.academy_base.utils.sql_helpers import create_index
from odoo.tools.misc import format_date
from odoo.osv.expression import AND
from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import ARCHIVED_DOMAIN, INCLUDE_ARCHIVED_DOMAIN
from ..utils.record_utils import ensure_recordset
from ..utils.helpers import sanitize_code, default_code

from logging import getLogger
from psycopg2 import DatabaseError as PsqlError
from datetime import datetime, date, time, timedelta
from pytz import utc, timezone

CODE_SEQUENCE="academy.training.action.enrolment.sequence"

_logger = getLogger(__name__)


class AcademyTrainingActionEnrolment(models.Model):
    """Enrolment allows the student to be linked to a training action"""

    _name = "academy.training.action.enrolment"
    _description = "Academy training action enrolment"

    _rec_name = "code"
    _order = "training_action_id, student_id, code ASC"
    _rec_names_search = ["code", "training_action_id", "student_id"]

    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "image.mixin",
        "ownership.mixin",
    ]

    _check_company_auto = True

    # Entity fields
    # -------------------------------------------------------------------------

    code = fields.Char(
        string="Enrolment code",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: default_code(self.env, CODE_SEQUENCE),
        help="Unique code automatically assigned to this enrolment",
        size=30,
        translate=False,
        tracking=True,
    )

    enrolment_date = fields.Datetime(
        string="Enrolment date",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: fields.Datetime.now(),
        help="Administrative date when the enrolment was recorded",
        tracking=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
        tracking=True,
    )

    comment = fields.Html(
        string="Internal notes",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Private staff-only notes; not shown to students or exported",
        sanitize=True,
        sanitize_attributes=False,
        strip_style=True,
        translate=False,
    )

    parent_action_id = fields.Many2one(
        string="Parent action",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Direct parent of the linked action; or the action itself.",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False
    )

    action_line_ids = fields.Many2many(
        string='Action lines',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Action lines linked to this enrolment",
        comodel_name='academy.training.action.line',
        relation='academy_training_action_enrolment_action_line_rel',
        column1='enrolment_id',
        column2='action_line_id',
        domain=[],
        context={}
    )

    training_modality_id = fields.Many2one(
        string="Training modality",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Learning modality for this enrolment",
        comodel_name="academy.training.modality",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    material = fields.Selection(
        string="Material",
        required=False,
        readonly=False,
        index=True,
        default="digital",
        help="Choose the format of the learning material",
        selection=[
            ("printed", "Printed"),
            ("digital", "Digital"),
        ],
    )

    material_status = fields.Selection(
        string='Material',
        required=True,
        readonly=False,
        index=True,
        default='na',
        help="Current status of material delivery.",
        selection=[
            ('pending', 'Pending Delivery'),
            ('delivered', 'Material Delivered'),
            ('na', 'Not Applicable / Digital'),
        ]
    )

    # Student information
    # -------------------------------------------------------------------------

    student_id = fields.Many2one(
        string="Student",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Student to enrol",
        comodel_name="academy.student",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    student_name = fields.Char(
        string="Student name",
        readonly=True,
        help="Name of the related student",
        related="student_id.name",
    )

    vat = fields.Char(
        string="Vat",
        related="student_id.vat",
        help="Student’s VAT number"
    )

    email = fields.Char(
        string="Email",
        related="student_id.email",
        help="Student’s email address"
    )

    phone = fields.Char(
        string="Phone",
        related="student_id.phone",
        help="Student’s phone number"
    )

    mobile = fields.Char(
        string="Mobile",
        related="student_id.mobile",
        help="Student’s mobile number"
    )

    zip = fields.Char(
        string="Zip",
        related="student_id.zip",
        help="Student’s ZIP/postal code"
    )

    # Training action information
    # -------------------------------------------------------------------------

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training action in which the student is enrolled",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):
        self.training_group_id = None
        if not self.training_action_id:
            self.action_line_ids = None
        else:
            self.action_line_ids = self.training_action_id.action_line_ids

    company_id = fields.Many2one(
        string="Company",
        related="training_action_id.company_id",
        help="Company of the related training action",
        store=True,
    )

    action_name = fields.Char(
        string="Training action name",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Name of the related training action",
        size=255,
        translate=True,
        related="training_action_id.name",
    )

    action_code = fields.Char(
        string="Internal code",
        help="Internal code of the training action",
        related="training_action_id.code",
    )

    date_start = fields.Datetime(
        string="Start of action",
        help="Start date/time of the training action",
        related="training_action_id.date_start",
    )

    date_stop = fields.Datetime(
        string="End of action",
        help="End date/time of the training action",
        related="training_action_id.date_stop",
    )

    training_program_id = fields.Many2one(
        string="Training program",
        help="Training program delivered in this action",
        related="training_action_id.training_program_id",
    )

    image_1024 = fields.Image(
        string="Image 1024",
        help="Training action image (1024 px)",
        related="training_action_id.image_1024",
    )

    image_512 = fields.Image(
        string="Image 512",
        help="Training action image (512 px)",
        related="training_action_id.image_512",
    )

    image_256 = fields.Image(
        string="Image 256",
        help="Training action image (256 px)",
        related="training_action_id.image_256",
    )

    image_128 = fields.Image(
        string="Image 128",
        help="Training action image (128 px)",
        related="training_action_id.image_128",
    )

    # -- Time interval: fields and logic
    # -------------------------------------------------------------------------

    register = fields.Datetime(
        string="Registration",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: fields.Datetime.now(),
        help="Date the enrolment becomes effective",
        tracking=True,
    )

    deregister = fields.Datetime(
        string="Deregistration",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Date the enrolment ends (leave empty if still ongoing)",
        tracking=True,
    )

    finalized = fields.Boolean(
        string="Finalized",
        required=True,
        readonly=True,
        index=False,
        default=False,
        help="Set to true when the enrolment has ended",
        compute="_compute_finalized",
        search="_search_finalized",
    )

    @api.depends("register", "deregister")
    def _compute_finalized(self):
        now = fields.Datetime.now()
        for record in self:
            record.finalized = record.deregister and record.deregister < now

    def _search_finalized(self, operator, value):
        pattern = _('Unsupported domain leaf ("finalized", "{}", "{}")')
        now = fields.Datetime.to_string(fields.Datetime.now())

        if operator == "!=":
            operator == "<>"

        if (operator == "=" and value) or (operator == "<>" and not value):
            domain = [
                "&",
                ("deregister", "<>", False),
                ("deregister", "<", now),
            ]

        elif (operator == "=" and not value) or (operator == "<>" and value):
            domain = [
                "|",
                ("deregister", "=", False),
                ("deregister", ">=", now),
            ]

        else:
            raise UserError(pattern.format(operator, value))

        return domain

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

    @api.depends("deregister")
    def _compute_available_until(self):
        one_day = timedelta(days=1)
        infinity = datetime.max

        for record in self:
            if record.deregister:
                deregister = datetime.combine(record.deregister, time.min)

                local = record.get_timezone()
                try:
                    deregister = local.localize(deregister)
                    deregister = deregister.astimezone(utc)
                    deregister = deregister + one_day
                except OverflowError:
                    deregister = infinity

                deregister = deregister.replace(tzinfo=None)
            else:
                deregister = infinity

            group_date_stop = record.training_group_id.date_stop or infinity
            action_date_stop = record.training_action_id.date_stop or infinity

            record.available_until = min(
                deregister, group_date_stop, action_date_stop
            )

    def get_timezone(self):
        self.ensure_one()

        company = self.company_id or self.training_action_id.company_id
        if company and company.partner_id and company.partner_id.tz:
            return timezone(company.partner_id.tz)

        return timezone('utc')

    color = fields.Integer(
        string="Color Index",
        required=True,
        readonly=True,
        index=False,
        default=10,
        help="Color index used in views based on enrolment dates",
        store=False,
        compute="_compute_color",
    )

    def _compute_color(self):
        today = date.today()

        for record in self:
            register = record.register.date()
            deregister = (record.deregister or date.max).date()

            if register <= today and deregister >= today:
                record.color = 10
            elif register >= today:
                record.color = 4
            else:
                record.color = 3

    # -- Computed field: is_current -------------------------------------------

    is_current = fields.Boolean(
        string="Is current",
        required=True,
        readonly=True,
        index=True,
        default=False,
        help="True when today is within the enrolment dates and it is active",
        compute="_compute_is_current",
        search="_search_is_current",
    )

    @api.depends("active", "register", "deregister")
    def _compute_is_current(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_current = (
                record.active
                and record.register <= now
                and (not record.deregister or record.deregister >= now)
            )

    @api.model
    def _search_is_current(self, operator, value):
        value = bool(value)  # Converts None to False to prevent errors

        now = fields.Datetime.now()

        # Toggle operator for negation if `value` is True
        if value is True:
            operator = TERM_OPERATORS_NEGATION[operator]
            value = not value

        if operator == "=":  # = False (not is current)
            domain = [
                "|",
                "|",
                ("active", "!=", True),
                ("register", ">", now),
                ("deregister", "<", now),
            ]
        else:
            domain = [
                "&",
                "&",
                ("active", "=", True),
                ("register", "<=", now),
                "|",
                ("deregister", ">=", now),
                ("deregister", "=", False),
            ]

        return domain

    # -- Computed field: lifespan ---------------------------------------------

    lifespan = fields.Char(
        string="Lifespan",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Formatted range of register and deregister dates",
        size=50,
        translate=False,
        compute="_compute_lifespan",
    )

    @api.depends("register", "deregister")
    @api.depends_context("uid")
    def _compute_lifespan(self):
        for record in self:
            if record.register and record.deregister:
                register_str = format_date(self.env, record.register)
                deregister_str = format_date(self.env, record.deregister)
                record.lifespan = f"{register_str} ‒ {deregister_str}"
            elif record.register:
                record.lifespan = format_date(self.env, record.register)
            else:
                record.lifespan = ""

    # -- Contraints -----------------------------------------------------------

    _sql_constraints = [
        (
            "check_date_order",
            'CHECK("deregister" IS NULL OR "register" <= "deregister")',
            "End date must be greater then date_start date",
        ),
        (
            "prevent_overlap",
            """
            EXCLUDE USING gist (
                training_action_id gist_int4_ops WITH =,
                student_id gist_int4_ops WITH =,
                (
                    tsrange(
                        register,
                        COALESCE(
                            deregister,
                            'infinity'::timestamp without time zone
                        )
                    )
                ) WITH &&
            ) DEFERRABLE INITIALLY IMMEDIATE
            """,
            "Student enrolments cannot overlap for the same action",
        ),
    ]

    @api.constrains(
        "student_id", "training_action_id", "register", "deregister"
    )
    def _check_unique_enrolment(self):
        """ """
        message = _("Student is already enroled in the training action")
        enrolment_obj = self.env["academy.training.action.enrolment"]

        for record in self:
            student_id = record.student_id.id
            action_id = record.training_action_id.id

            domains = [[("id", "<>", record.id)]]

            domains.append([("student_id", "=", student_id)])
            domains.append([("training_action_id", "=", action_id)])
            domains.append(
                [
                    "|",
                    ("deregister", "=", False),
                    ("deregister", ">", record.register),
                ]
            )

            if not record.deregister:
                domains.append([("register", "<", record.deregister)])

            if enrolment_obj.search(AND(domains)):
                ValidationError(message)

    # -- Methods overrides ----------------------------------------------------

    @api.depends(
        "training_action_id",
        "training_action_id.code",
        "student_id",
        "student_id.signup_code",
    )
    def _compute_display_name(self):
        for record in self:
            training = record.training_action_id.code
            student = record.student_id.signup_code
            if training and student:
                training = training.strip().upper()
                student = student.strip().upper()
                record.display_name = f"{training} - {student}"

            else:
                record.display_name = _("New enrolment")

    # Overridden methods
    # -------------------------------------------------------------------------

    def init(self):
        """
        Ensures the custom index exists in the database.
        """

        fields = ["active", "deregister", "register"]
        create_index(
            self.env,
            self._table,
            fields,
            unique=False,
            name=f'{self._table}__{'search_active_by_dates_index'}',
        )

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

        parent = super(AcademyTrainingActionEnrolment, self)

        try:
            result = parent._create(values)
        except PsqlError as ex:
            if "ATE01" in str(ex.pgcode):
                error = _("Enrolment is outside the range of training action")
                raise ValidationError(error)
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

        parent = super(AcademyTrainingActionEnrolment, self)

        try:
            result = parent._write(values)
        except PsqlError as ex:
            if "ATE01" in str(ex.pgcode):
                error = _("Enrolment is outside the range of training action")
                raise ValidationError(error)
            else:
                raise

        return result

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        sanitize_code(values_list, "upper")

        self._perform_a_full_enrollment(values_list)

        parent = super(AcademyTrainingActionEnrolment, self)
        result = parent.create(values_list)

        return result

    def write(self, values):
        """Overridden method 'write'"""

        sanitize_code(values, "upper")

        self._check_that_the_student_is_not_the_template(values)

        parent = super(AcademyTrainingActionEnrolment, self)
        result = parent.write(values)

        return result

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """Prevents new record of the inherited (_inherits) models will
        be created. It also adds the following sequence value.

        Assign a temporaty student to allow the copy.
        """

        parent = super(AcademyTrainingActionEnrolment, self)

        xmlid = "academy_base.academy_student_default_template"
        imd_obj = self.env["ir.model.data"]
        student = imd_obj.xmlid_to_object(xmlid, raise_if_not_found=True)

        default = dict(default or {})
        default.update(
            {
                "student_id": student.id,
                "training_action_id": self.training_action_id.id,
                "code": self._default_code(),
            }
        )

        return parent.copy(default)

    # Public methods
    # -------------------------------------------------------------------------

    def go_to_student(self):
        student_set = self.mapped("student_id")

        if not student_set:
            msg = _("There is no students")
            raise UserError(msg)
        else:
            view_act = {
                "type": "ir.actions.act_window",
                "res_model": "academy.student",
                "target": "current",
                "nodestroy": True,
                "domain": [("id", "in", student_set.mapped("id"))],
            }

            if len(student_set) == 1:
                view_act.update(
                    {
                        "name": student_set.name,
                        "view_mode": "form,kanban,list",
                        "res_id": student_set.id,
                        "view_type": "form",
                    }
                )

            else:
                view_act.update(
                    {
                        "name": _("Students"),
                        "view_mode": "list",
                        "res_id": None,
                        "view_type": "form",
                    }
                )

            return view_act

    def copy_to(self, action_set, origin_set=False):
        if not origin_set:
            origin_set = self

        action_set = ensure_recordset(
            self.env, action_set, 'academy.training.action'
        )
        origin_set = ensure_recordset(self.env, origin_set, self._name)

        for enrolment in origin_set:
            for action in action_set:
                register = enrolment.register
                deregister = enrolment.deregister

                if (
                    register < action.date_start
                    or register >= action.date_stop
                ):
                    register = action.date_start

                if (
                    deregister > action.date_stop
                    or deregister <= action.date_start
                    or deregister <= register
                ):
                    deregister = action.date_stop

                register = register.strftime("")

    def fetch_enrollments(
        self,
        students=None,
        training_actions=None,
        point_in_time=None,
        archived=False,
    ):
        enrolment_set = self.env["academy.training.action.enrolment"]

        domains = []

        if students:
            domain = create_domain_for_ids("student_id", students)
            domains.append(domain)

        if training_actions:
            domain = create_domain_for_ids(
                "training_action_id", training_actions
            )
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
            enrolment_set = enrolment_set.search(AND(domains))

        return enrolment_set

    # Auxiliary methods
    # -------------------------------------------------------------------------

    def _check_that_the_student_is_not_the_template(self, values):
        """When registrations are duplicated, the temporary student is
        assigned to them. This method generates a validation error when one of
        them tries to be modified without establishing a real student for it.
        """

        msg = _("You must assign a real student to each of the enrolments.")

        temp_student_xid = "academy_base.academy_student_default_template"
        temp_student = self.env.ref(temp_student_xid)

        if temp_student.id in self.student_id.ids:
            new_student_id = values.get("student_id", False)
            if not new_student_id or new_student_id == temp_student.id:
                raise ValidationError(msg)

    @api.model
    def remove_temporary_student_enrollments(self):
        """When registrations are duplicated, the temporary student is
        assigned to them. These must be edited to establish the corresponding
        student or, otherwise, a scheduled task will invoke this method to
        remove them.
        """

        temp_student_xid = "academy_base.academy_student_default_template"
        temp_student = self.env.ref(temp_student_xid)

        one_hour_ago = datetime.now() - timedelta(hours=1)
        one_hour_ago = fields.Datetime.to_string(one_hour_ago)

        student_domain = [
            "&",
            ("student_id", "=", temp_student.id),
            "|",
            ("create_date", "=", False),
            ("create_date", "<", one_hour_ago),
        ]
        domain = AND([INCLUDE_ARCHIVED_DOMAIN, student_domain])
        enrolment_obj = self.env["academy.training.action.enrolment"]
        enrolment_set = enrolment_obj.search(domain)

        _logger.info("Temporary student enrolments will be removed {}")
        enrolment_set.unlink()

    # -------------------------------------------------------------------------

    @api.model
    def _perform_a_full_enrollment(self, values_list):
        for values in values_list:
            action_id = values.get("training_action_id", None)

            if action_id:
                action_obj = self.env["academy.training.action"]
                action_set = action_obj.browse(action_id)

                # if action_set and action_set.program_line_ids:
                #     competency_ids = action_set.competency_unit_ids.ids
                #     values["competency_unit_ids"] = [(6, 0, competency_ids)]

    @api.model
    def _ensure_enrolment_date(self, vals_list):
        now = fields.Datetime.now()
        for values in vals_list:
            if not values.get("enrolment_date"):
                values["enrolment_date"] = now

    @api.model
    def _ensure_enrolment_data(self, values):
        if not values.get("code"):
            company_id = values.get("company_id") or self.env.company.id
            values["code"] = self._next_signup_code(company_id)
            values["barcode"] = values["code"]

        if not values.get("enrolment_date", False):
            self._ensure_enrolment_date([values])
