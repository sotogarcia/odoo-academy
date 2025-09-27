# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module contains the academy.training.action.enrolment Odoo model which
stores all training action enrolment attributes and behavior.
"""

from logging import getLogger
from datetime import date, datetime, timedelta
from psycopg2 import DatabaseError as PsqlError

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _, _lt
from odoo.exceptions import UserError
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.osv.expression import TERM_OPERATORS_NEGATION
from odoo.exceptions import ValidationError

from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import ARCHIVED_DOMAIN, INCLUDE_ARCHIVED_DOMAIN
from odoo.addons.academy_base.utils.sql_helpers import create_index


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingActionEnrolment(models.Model):
    """Enrolment allows the student to be linked to a training action"""

    MSG_ATE01 = _lt("Enrolment is outside the range of training action")

    _name = "academy.training.action.enrolment"
    _description = "Academy training action enrolment"

    _rec_name = "code"
    _order = "code ASC"

    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "image.mixin",
        "ownership.mixin",
    ]

    _check_company_auto = True

    company_id = fields.Many2one(
        string="Company", related="training_action_id.company_id", store=True
    )

    # pylint: disable=locally-disabled, W0212
    code = fields.Char(
        string="Code",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self._default_code(),
        help="Enter new code",
        size=30,
        translate=False,
        tracking=True,
    )

    comment = fields.Html(
        string='Internal notes',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=('Private notes for staff only. Not shown to students, '
          'not exported, and excluded from printed reports.'),
        sanitize=True,
        sanitize_attributes=False,
        strip_style=True,
        translate=False,
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

    student_id = fields.Many2one(
        string="Student",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Choose enroled student",
        comodel_name="academy.student",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Choose training action in which the student will be enroled",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    # pylint: disable=locally-disabled, W0108
    register = fields.Date(
        string="Signup",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: fields.Date.context_today(self),
        help="Date in which student has been enroled",
        tracking=True,
    )

    deregister = fields.Date(
        string="Deregister",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Date in which student has been unsubscribed",
        tracking=True,
    )

    training_modality_ids = fields.Many2many(
        string="Training modalities",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose training modalities",
        comodel_name="academy.training.modality",
        relation="academy_training_action_enrolment_training_modality_rel",
        column1="enrolment_id",
        column2="modality_id",
        domain=[],
        context={},
        tracking=True,
    )

    training_modality_str = fields.Char(
        string="Modality",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Name of the modality if it is single or "Mixed" otherwise',
        size=255,
        translate=True,
        compute="_compute_training_modality_str",
    )

    @api.depends("training_modality_ids")
    def _compute_training_modality_str(self):
        for record in self:
            if not record.training_modality_ids:
                record.training_modality_str = None
            elif len(record.training_modality_ids) == 1:
                record.training_modality_str = (
                    record.training_modality_ids.name
                )
            else:
                record.training_modality_str = (
                    record.training_modality_str
                ) = _("Mixed")

    # This will be used in form view to compute domain
    available_modality_ids = fields.Many2many(
        string="Available modalities",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Available training modalities",
        comodel_name="academy.training.modality",
        relation="academy_training_action_enrolment_available_modalities_rel",
        column1="enrolment_id",
        column2="modality_id",
        domain=[],
        context={},
        compute="_compute_available_modality_ids",
    )

    @api.depends("training_action_id")
    def _compute_available_modality_ids(self):
        modality_domain = []
        modality_obj = self.env["academy.training.modality"]
        modality_set = modality_obj.search(modality_domain)

        for record in self:
            action = record.training_action_id
            if action and action.training_modality_ids:
                record.available_modality_ids = action.training_modality_ids
            else:
                record.available_modality_ids = modality_set

    material = fields.Selection(
        string="Material",
        required=False,
        readonly=False,
        index=True,
        default="digital",
        help="Choose educational material format",
        selection=[("printed", "Printed"), ("digital", "Digital")],
    )

    # It is necessary to keep the difference with the name of the activity
    student_name = fields.Char(
        string="Student name",
        readonly=True,
        help="Show the name of the related student",
        related="student_id.name",
    )

    vat = fields.Char(string="Vat", related="student_id.vat")

    email = fields.Char(string="Email", related="student_id.email")

    phone = fields.Char(string="Phone", related="student_id.phone")

    mobile = fields.Char(string="Mobile", related="student_id.mobile")

    zip = fields.Char(string="Zip", related="student_id.zip")

    # It is necessary to keep the difference with the name of the activity
    name = fields.Char(
        string="Training action name",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Show the name of the related training action",
        size=255,
        translate=True,
        related="training_action_id.name",
    )

    finalized = fields.Boolean(
        string="Finalized",
        required=True,
        readonly=True,
        index=False,
        default=False,
        help="True if period is completed",
        compute="_compute_finalized",
        search="_search_finalized",
    )

    name = fields.Char(
        string="Action name",
        help="Enter new name",
        related="training_action_id.name",
    )

    code = fields.Char(
        string="Internal code",
        help="Enter new internal code",
        related="training_action_id.code",
    )

    start = fields.Datetime(
        string="Start",
        help="Start date of an event, without time for full day events",
        related="training_action_id.start",
    )

    end = fields.Datetime(
        string="End",
        help="Stop date of an event, without time for full day events",
        related="training_action_id.end",
    )

    training_program_id = fields.Many2one(
        string="Training program",
        help="Training program will be imparted in this action",
        related="training_action_id.training_program_id",
    )

    image_1024 = fields.Image(
        string="Image 1024",
        related="training_action_id.image_1024",
    )

    image_512 = fields.Image(
        string="Image 512",
        related="training_action_id.image_512",
    )

    image_256 = fields.Image(
        string="Image 256",
        related="training_action_id.image_256",
    )

    image_128 = fields.Image(
        string="Image 128",
        related="training_action_id.image_128",
    )

    @api.depends("register", "deregister")
    def _compute_finalized(self):
        now = fields.Date.today()
        for record in self:
            record.finalized = record.deregister and record.deregister < now

    def _search_finalized(self, operator, value):
        pattern = _('Unsupported domain leaf ("finalized", "{}", "{}")')
        now = fields.Date.to_string(fields.Date.today())

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

    color = fields.Integer(
        string="Color Index",
        required=True,
        readonly=True,
        index=False,
        default=10,
        help="Display color based on dependency and status",
        store=False,
        compute=lambda self: self._compute_color(),
    )

    def _compute_color(self):
        today = date.today()

        for record in self:
            register = record.register
            deregister = record.deregister or date.max

            if register <= today and deregister >= today:
                record.color = 10
            elif register >= today:
                record.color = 4
            else:
                record.color = 3

    is_current = fields.Boolean(
        string="Is current",
        required=True,
        readonly=True,
        index=True,
        default=False,
        help="Indicates if the enrolment is currently active",
        compute="_compute_is_current",
        search="_search_is_current",
    )

    @api.depends("active", "register", "deregister")
    def _compute_is_current(self):
        today = fields.Date.today()
        for record in self:
            record.is_current = (
                record.active
                and record.register <= today
                and (not record.deregister or record.deregister >= today)
            )

    @api.model
    def _search_is_current(self, operator, value):
        value = bool(value)  # Converts None to False to prevent errors

        today = fields.Date.today()

        # Toggle operator for negation if `value` is True
        if value is True:
            operator = TERM_OPERATORS_NEGATION[operator]
            value = not value

        if operator == "=":  # = False (not is current)
            domain = [
                "|",
                "|",
                ("active", "!=", True),
                ("register", ">", today),
                ("deregister", "<", today),
            ]
        else:
            domain = [
                "&",
                "&",
                ("active", "=", True),
                ("register", "<=", today),
                "|",
                ("deregister", ">=", today),
                ("deregister", "=", False),
            ]

        return domain

    # ---------------------------- ONCHANGE EVENTS ----------------------------

    @api.onchange("training_action_id")
    def _onchange_training_action_id(self):
        modality_path = "training_action_id.training_modality_ids"

        for record in self:
            if self.training_action_id:
                self.training_modality_ids = self.mapped(modality_path)
                self.deregister = self.training_action_id.end
            else:
                self.training_modality_ids = None
                self.deregister = None

    # -------------------------- AUXILIARY METHODS ----------------------------

    @api.model
    def _default_code(self):
        """Get next value for sequence"""

        seqxid = "academy_base.ir_sequence_academy_action_enrolment"
        seqobj = self.env.ref(seqxid)

        result = seqobj.next_by_id()

        return result

    def name_get(self):
        result = []

        for record in self:
            if record.student_id and record.training_action_id:
                training = record.training_action_id.name
                student = record.student_id.name

                name = "{} - {}".format(training, student)

            else:
                name = _("New training action enrolment")

            result.append((record.id, name))

        return result

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

    _sql_constraints = [
        (
            "check_date_order",
            'CHECK("deregister" IS NULL OR "register" <= "deregister")',
            "End date must be greater then start date",
        ),
        (
            "prevent_overlap",
            """EXCLUDE USING gist (
                training_action_id WITH =,
                student_id WITH =,
                tsrange(
                    register,
                    COALESCE(deregister, 'infinity'::date),
                    '[]'
                ) WITH &&
            )""",
            (
                "Student enrollments cannot overlap in time for the same "
                "training action"
            ),
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

    @api.model
    def _ensure_recordset(self, model, sources):
        source_obj = self.env[model]

        if isinstance(sources, int):
            source_set = source_obj.browse(sources)
        elif isinstance(sources, (list, tuple)):
            action_domain = [("id", "in", sources)]
            source_set = source_obj.search(action_domain)
        else:
            msg = _("The source recordset must correspond to the model {}")
            assert isinstance(sources, type(source_obj)), msg.format(model)
            source_set = sources

        return source_set

    def copy_to(self, action_set, origin_set=False):
        if not origin_set:
            origin_set = self

        action_set = self._ensure_recordset(action_set)
        origin_set = self._ensure_recordset(origin_set or self)

        for enrolment in origin_set:
            for action in action_set:
                register = enrolment.register
                deregister = enrolment.deregister

                if register < action.start or register >= action.stop:
                    register = action.start

                if (
                    deregister > action.stop
                    or deregister <= action.start
                    or deregister <= register
                ):
                    deregister = action.stop

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
                raise ValidationError(self.MSG_ATE01)
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
                raise ValidationError(self.MSG_ATE01)
            else:
                raise

        return result

    def write(self, values):
        """Overridden method 'write'"""
        self._check_that_the_student_is_not_the_template(values)

        parent = super(AcademyTrainingActionEnrolment, self)
        result = parent.write(values)

        return result

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

    # -------------------------------------------------------------------------
    # Copy related methods
    # -------------------------------------------------------------------------

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

    def _check_that_the_student_is_not_the_template(self, values):
        """When registrations are duplicated, the temporary student is
        assigned to them. This method generates a validation error when one of
        them tries to be modified without establishing a real student for it.
        """

        msg = _("You must assign a real student to each of the enrollments.")

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
        enrollment_obj = self.env["academy.training.action.enrolment"]
        enrollment_set = enrollment_obj.search(domain)

        _logger.info("Temporary student enrollments will be removed {}")
        enrollment_set.unlink()

    # -------------------------------------------------------------------------

    @api.model
    def _perform_a_full_enrollment(self, values):
        action_id = values.get("training_action_id", None)

        if action_id:
            action_obj = self.env["academy.training.action"]
            action_set = action_obj.browse(action_id)

            # if action_set and action_set.competency_unit_ids:
            #     competency_ids = action_set.competency_unit_ids.ids
            #     values["competency_unit_ids"] = [(6, 0, competency_ids)]

    @api.model_create_multi
    def create(self, value_list):
        """Overridden method 'create'"""

        # for values in value_list:
        #     if "competency_unit_ids" not in values:
        #         self._perform_a_full_enrollment(values)

        parent = super(AcademyTrainingActionEnrolment, self)
        result = parent.create(value_list)

        return result
