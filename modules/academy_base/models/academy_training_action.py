# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.training.action Odoo model which stores
all training action attributes and behavior.
"""


from odoo.tools.translate import _

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import ARCHIVED_DOMAIN, INCLUDE_ARCHIVED_DOMAIN

from logging import getLogger
from pytz import utc
from uuid import uuid4
from psycopg2 import Error as PsqlError

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingAction(models.Model):
    """The training actions represent several groups of students for the same
    training activity
    """

    MSG_ATA01 = _(
        "There are enrollments that are outside the range of "
        "training action"
    )

    _name = "academy.training.action"
    _description = "Academy training action"

    _rec_name = "action_name"
    _order = "action_name ASC"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "academy.abstract.observable",
        "academy.abstract.training",
        "ownership.mixin",
    ]

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

    action_name = fields.Char(
        string="Action name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new name",
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
        help="Enables/disables the record",
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
        track_visibility="always",
    )

    # pylint: disable=locally-disabled, w0212
    start = fields.Datetime(
        string="Start",
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
    end = fields.Datetime(
        string="End",
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_end(),
        help="Stop date of an event, without time for full day events",
    )

    def default_end(self):
        now = fields.Datetime.now()
        now = fields.Datetime.context_timestamp(self, now)
        now = now.replace(hour=23, minute=59, second=59)

        return now.astimezone(utc).replace(tzinfo=None)

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

    training_modality_ids = fields.Many2many(
        string="Training modalities",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose training modalities",
        comodel_name="academy.training.modality",
        relation="academy_training_action_training_modality_rel",
        column1="training_action_id",
        column2="training_modality_id",
        domain=[],
        context={},
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

    training_activity_id = fields.Many2one(
        string="Training activity",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Training activity will be imparted in this action",
        comodel_name="academy.training.activity",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    action_code = fields.Char(
        string="Internal code",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Enter new internal code",
        size=30,
        translate=False,
    )

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

    training_action_enrolment_ids = fields.One2many(
        string="Action enrolments",
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

    action_resource_ids = fields.Many2many(
        string="Action resources",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.resource",
        relation="academy_training_action_training_resource_rel",
        column1="training_action_id",
        column2="training_resource_id",
        domain=[],
        context={},
    )

    available_resource_ids = fields.Many2manyView(
        string="Available action resources",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.resource",
        relation="academy_training_action_available_resource_rel",
        column1="training_action_id",
        column2="training_resource_id",
        domain=[],
        context={},
        copy=False,
    )

    student_ids = fields.Many2manyView(
        string="Students",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Show the students have been enrolled in this training action",
        comodel_name="academy.student",
        relation="academy_training_action_student_rel",
        column1="training_action_id",
        column2="student_id",
        domain=[],
        context={},
        copy=False,
    )

    enrolment_count = fields.Integer(
        string="Enrolment count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Show number of enrolments",
        compute="_compute_training_action_enrolment_count",
        search="_search_training_action_enrolment_count",
    )

    @api.depends("training_action_enrolment_ids")
    def _compute_training_action_enrolment_count(self):
        counts = one2many_count(self, "training_action_enrolment_ids")

        for record in self:
            record.reservation_count = counts.get(record.id, 0)

    @api.model
    def _search_training_action_enrolment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(
            self.search([]), "training_action_enrolment_ids"
        )
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    @api.onchange("training_action_enrolment_ids")
    def _onchange_training_action_enrolment_ids(self):
        self._compute_training_action_enrolment_count()

    excess = fields.Integer(
        string="Excess",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help=_(
            "Maximum number of students who can be invited to use this "
            "feature at the same time"
        ),
    )

    # ------------------------- ACTIVITY RELATED FIELDS -----------------------
    # _inherits from training activity raises an error with multicompany

    name = fields.Char(string="Name", related="training_activity_id.name")

    professional_family_id = fields.Many2one(
        string="Professional family",
        related="training_activity_id.professional_family_id",
    )

    professional_area_id = fields.Many2one(
        string="Professional area",
        related="training_activity_id.professional_area_id",
    )

    qualification_level_id = fields.Many2one(
        string="Qualification level",
        related="training_activity_id.qualification_level_id",
    )

    attainment_id = fields.Many2one(
        string="Educational attainment",
        related="training_activity_id.attainment_id",
    )

    activity_code = fields.Char(
        string="Activity code", related="training_activity_id.activity_code"
    )

    general_competence = fields.Text(
        string="General competence",
        related="training_activity_id.general_competence",
    )

    professional_field_id = fields.Many2one(
        string="Professional field",
        related="training_activity_id.professional_field_id",
    )

    professional_sector_ids = fields.Many2many(
        string="Professional sectors",
        related="training_activity_id.professional_sector_ids",
    )

    competency_unit_ids = fields.One2many(
        string="Competency units",
        related="training_activity_id.competency_unit_ids",
    )

    competency_unit_count = fields.Integer(
        string="Number of competency units",
        related="training_activity_id.competency_unit_count",
    )

    # ------------------------------ CONSTRAINS -------------------------------

    _sql_constraints = [
        (
            "unique_action_code",
            "UNIQUE(action_code)",
            _("The given action code already exists"),
        ),
        (
            "check_date_order",
            'CHECK("end" IS NULL OR "start" < "end")',
            "End date must be greater then start date",
        ),
        (
            "USERS_GREATER_OR_EQUAL_TO_ZERO",
            "CHECK(seating >= 0)",
            "The number of users must be greater than or equal to zero",
        ),
        ("unique_token", "UNIQUE(token)", "The token must be unique."),
    ]

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
        #     'training_activity_id': self.training_activity_id.id
        # })
        #
        if "action_code" not in defaults:
            defaults["action_code"] = uuid4().hex.upper()

        if "action_name" not in defaults:
            defaults["action_name"] = "{} - {}".format(
                self.action_name, action_set.id + 1
            )

        rec = super(AcademyTrainingAction, self).copy(defaults)
        return rec

    @api.model
    def _create(self, values):
        """Overridden low-level method '_create' to handle custom PostgreSQL
        exceptions.

        This method handles custom PostgreSQL exceptions, specifically catching
        the exception with code 'ATE01', triggered by a database trigger that
        validates enrollment dates in training actions.

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
        validates enrollment dates in training actions.

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

        parent = super(AcademyTrainingAction, self)
        result = parent.create(value_list)

        result.update_enrolments()

        return result

    def write(self, values):
        """Overridden method 'write'"""

        parent = super(AcademyTrainingAction, self)
        result = parent.write(values)

        self.update_enrolments()

        return result

    # --------------------------- PUBLIC METHODS ------------------------------

    def update_enrolments(self, force=False):
        dtformat = "%Y-%m-%d %H:%M:%S.%f"

        for record in self:
            enrol_set = record.training_action_enrolment_ids

            # Enrolment start must be great or equal than record start
            target_set = enrol_set.filtered(lambda r: r.start < record.start)
            target_set.write({"start": record.start.strftime(dtformat)})

            # Enrolment end must be less or equal than record end
            # NOTE: end date can be null
            if record.end:
                target_set = enrol_set.filtered(
                    lambda r: r.end and r.end > record.end
                )
                target_set.write({"end": record.end.strftime(dtformat)})

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

    def show_training_action_enrolments(self):
        self.ensure_one()

        act_xid = "academy_base.action_training_action_enrolment_act_window"
        action = self.env.ref(act_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({"default_training_action_id": self.id})

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [("training_action_id", "=", self.id)]])

        action_values = {
            "name": "{} {}".format(_("Enrolled in"), self.name),
            "type": action.type,
            "help": action.help,
            "domain": domain,
            "context": ctx,
            "res_model": action.res_model,
            "target": action.target,
            "view_mode": action.view_mode,
            "search_view_id": action.search_view_id.id,
            "target": "current",
        }

        return action_values

    def copy_activity_image(self):
        for record in self:
            if not record.training_activity_id:
                continue

            if not record.training_activity_id.image_1920:
                continue

            record.image_1920 = record.training_activity_id.image_1920
            record.image_1024 = record.training_activity_id.image_1024
            record.image_512 = record.training_activity_id.image_512
            record.image_256 = record.training_activity_id.image_256
            record.image_128 = record.training_activity_id.image_128

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
