# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

"""
academy.training.action.enrolment

<Enrolment> records are attached to training actions that may be hierarchical.

Relationship model
------------------
- A training action can have zero (0) or more child actions.
- An <enrolment> must always target the *last* actionable unit (a leaf action).

Field semantics
---------------
- training_action_id:
    The leaf `academy.training.action` the learner actually enrolls in.
    This MUST be a leaf (i.e., it cannot have child actions).

- parent_action_id:
    The direct parent action of `training_action_id` when the latter is a child.
    If `training_action_id` has no parent (no children exist in that branch),
    then `parent_action_id` MUST be the same record as `training_action_id`.

Formal invariants
-----------------
Let A = training_action_id and P = A.parent_id.

1) A.child_ids == False
   (<enrolment> cannot point to a non-leaf action)

2) parent_action_id == (P if P else A)

These invariants must hold on create and on any update that changes A.

Rationale
---------
Having both fields denormalizes the hierarchy for fast reporting and grouping:
- training_action_id tells "where the learner really sits" (leaf).
- parent_action_id allows easy aggregation by the immediate parent or by the
  action itself when there is no child level.

Examples
--------
1) Action A with child B:
   training_action_id = B
   parent_action_id   = A

2) Action A with no children:
   training_action_id = A
   parent_action_id   = A

Implementation notes
--------------------
- Enforce the invariants with an @api.constrains on training_action_id and
  parent_action_id.
- Recompute/validate parent_action_id whenever training_action_id changes.
- Consider SQL/indexes on (parent_action_id, training_action_id) for common
  reporting queries.
"""

from odoo import models, fields, api
from odoo.tools.misc import format_date
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import TRUE_DOMAIN
from odoo.osv.expression import TERM_OPERATORS_NEGATION, AND
from ..utils.helpers import sanitize_code, default_code
from ..utils.sql_helpers import create_index
from ..utils.record_utils import (
    ARCHIVED_DOMAIN,
    INCLUDE_ARCHIVED_DOMAIN,
    ensure_recordset,
    create_domain_for_ids,
    create_domain_for_interval,
)

from datetime import datetime, date, time, timedelta
from pytz import timezone, utc

from logging import getLogger


_CODE_SEQUENCE = "academy.training.action.enrolment.sequence"

_logger = getLogger(__name__)


class AcademyTrainingActionEnrolment(models.Model):
    """Enrolment allows the student to be linked to a training action"""

    _name = "academy.training.action.enrolment"
    _description = "Academy training action enrolment"

    _rec_name = "code"
    _order = "training_action_id, student_id, code ASC"
    _rec_names_search = ["code", "training_action_id", "student_id"]

    _inherit = [
        "ownership.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "image.mixin",
    ]

    _check_company_auto = True

    # Entity fields
    # -------------------------------------------------------------------------

    code = fields.Char(
        string="Enrolment code",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: default_code(self.env, _CODE_SEQUENCE),
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
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="Direct parent of the linked action; or the action itself.",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        compute="_compute_parent_action_id",
        store=True,
    )

    @api.depends("training_action_id", "training_action_id.parent_id")
    def _compute_parent_action_id(self):
        for record in self:
            record.parent_action_id = (
                record.training_action_id.parent_id
                or record.training_action_id
            )

    action_line_ids = fields.Many2many(
        string="Action lines",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Action lines linked to this enrolment",
        comodel_name="academy.training.action.line",
        relation="academy_training_action_enrolment_action_line_rel",
        column1="enrolment_id",
        column2="action_line_id",
        domain=[],
        context={},
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
        tracking=True,
    )

    material_status = fields.Selection(
        string="Material",
        required=True,
        readonly=False,
        index=True,
        default="na",
        help="Current status of material delivery.",
        selection=[
            ("pending", "Pending Delivery"),
            ("delivered", "Material Delivered"),
            ("na", "Not Applicable / Digital"),
        ],
        tracking=True,
    )

    full_enrolment = fields.Boolean(
        string="Full enrolment",
        required=False,
        readonly=False,
        index=True,
        default=True,
        help="If active, the student will be automatically enrolled in all "
        "modules of the training program.",
        tracking=True,
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
        tracking=True,
    )

    student_name = fields.Char(
        string="Student name",
        readonly=True,
        help="Name of the related student",
        related="student_id.name",
    )

    vat = fields.Char(
        string="VAT", related="student_id.vat", help="Student’s VAT number"
    )

    email = fields.Char(
        string="Email",
        related="student_id.email",
        help="Student’s email address",
    )

    phone = fields.Char(
        string="Phone",
        related="student_id.phone",
        help="Student’s phone number",
    )

    mobile = fields.Char(
        string="Mobile",
        related="student_id.mobile",
        help="Student’s mobile number",
    )

    zip = fields.Char(
        string="Zip",
        related="student_id.zip",
        help="Student’s ZIP/postal code",
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
        domain=[("child_ids", "=", False)],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    @api.onchange("training_action_id")
    def _onchange_training_action_id(self):
        self.training_modality_id = (
            self.training_action_id.training_modality_id
        )

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
        string="Code",
        help="Code of the training action",
        related="training_action_id.code",
    )

    date_start = fields.Datetime(
        string="Start of action",
        help="Start date/time of the training action",
        related="training_action_id.date_start",
        store=True,
    )

    date_stop = fields.Datetime(
        string="End of action",
        help="End date/time of the training action",
        related="training_action_id.date_stop",
        store=True,
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

    available_line_ids = fields.One2many(
        string="Available lines",
        readonly=True,
        help="Programme lines included in this enrolment",
        related="training_action_id.action_line_ids",
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
            record.finalized = record.deregister and (record.deregister < now)

    def _search_finalized(self, operator, value):
        pattern = self.env._(
            'Unsupported domain leaf ("finalized", "{}", "{}")'
        )
        now = fields.Datetime.now()

        if operator == "!=":
            operator = "<>"

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
        help="00:00 the day after, or indefinity for open enrolments.",
        compute="_compute_available_until",
        store=True,
    )

    @api.depends(
        "deregister", "training_action_id", "training_action_id.date_stop"
    )
    def _compute_available_until(self):
        infinity = datetime.max

        for record in self:
            deregister = record.deregister or infinity
            action_date_stop = record.training_action_id.date_stop or infinity
            record.available_until = min(deregister, action_date_stop)

    lifespan = fields.Char(
        string="Lifespan",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Formatted range of registration and deregistration dates",
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

    # -- Business fields and logic
    # -------------------------------------------

    available_action_ids = fields.Many2many(
        string="Available actions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Actions that the student may be assigned to: leaf actions "
        "(no children). If a parent action is set, show only its children.",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        compute="_compute_available_action_ids",
    )

    @api.depends("parent_action_id", "parent_action_id.child_ids")
    def _compute_available_action_ids(self):
        action_obj = self.env["academy.training.action"]
        base_domain = [("child_ids", "=", False)]
        parent_ids = {
            record.parent_action_id.id
            for record in self
            if record.parent_action_id
        }
        without_parent = any(not record.parent_action_id for record in self)

        child_action_set = action_obj.browse()
        full_action_set = action_obj.browse()

        if parent_ids:
            domain = AND(
                [base_domain, [("parent_id", "in", list(parent_ids))]]
            )
            child_action_set = action_obj.search(domain)

        if without_parent:
            full_action_set = action_obj.search(base_domain)

        for record in self:
            if record.parent_action_id:
                record.available_action_ids = child_action_set.filtered(
                    lambda r: r.parent_id == record.parent_action_id
                )
            else:
                record.available_action_ids = full_action_set

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
        infinity = datetime.max
        now = fields.Datetime.now()
        for record in self:
            register = record.register
            deregister = record.deregister or infinity

            if register < now and deregister >= now:
                record.color = 10
            elif register >= now:
                record.color = 4
            else:
                record.color = 3

    # -- Contraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            "check_date_order",
            'CHECK("deregister" IS NULL OR "register" <= "deregister")',
            "End date must be greater than start date",
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
        (
            "within_action_time_window",
            """
            CHECK(
                (register >= date_start)
                AND
                (
                    COALESCE(
                        deregister,
                        'infinity'::timestamp without time zone
                    )
                    <=
                    COALESCE(
                        date_stop,
                        'infinity'::timestamp without time zone
                    )
                )
            )
            """,
            "Student enrolments must be within the time window of the "
            "training action.",
        ),
    ]

    @api.constrains(
        "student_id", "training_action_id", "register", "deregister"
    )
    def _check_unique_enrolment(self):
        """Prevent overlapping enrolments for the same student and action."""
        message = self.env._(
            "Student is already enrolled in the training action"
        )
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

            if record.deregister:
                domains.append([("register", "<", record.deregister)])

            if enrolment_obj.search(AND(domains)):
                raise ValidationError(message)

    @api.constrains("training_action_id")
    def _check_training_action_is_leaf(self):
        message = self.env._(
            "Enrolments must be linked to a leaf training action "
            "(an action without child actions)."
        )
        for record in self:
            action = record.training_action_id
            if action and action.child_ids:
                raise ValidationError(message)

    @api.constrains("student_id", "company_id")
    def _check_student_has_signup_in_company(self):
        """Ensure each (student, company) pair in this batch has a signup row.

        Efficient, batched validation:
        - Collect required (student_id, company_id) pairs in one pass.
        - Fetch existing signup pairs with a single grouped query.
        - If any required pair is missing, raise a single ValidationError.
        """

        # 1) Collect all required pairs (student, company)
        student_ids, company_ids, required_pairs = set(), set(), set()
        for record in self:
            student_id = record.student_id.id
            company_id = record.company_id.id
            if student_id and company_id:
                student_ids.add(student_id)
                company_ids.add(company_id)
                required_pairs.add((student_id, company_id))

        if not required_pairs:
            return

        # 2) Fetch existing signup pairs (single grouped query)
        signup_obj = self.env["academy.student.signup"].sudo()
        domain = [
            ("student_id", "in", list(student_ids)),
            ("company_id", "in", list(company_ids)),
        ]
        rows = signup_obj.read_group(
            domain=domain,
            fields=["id:count"],
            groupby=["student_id", "company_id"],
            lazy=False,
        )

        # 3) Verify that all required pairs exist
        found_pairs = {(r["student_id"][0], r["company_id"][0]) for r in rows}
        missing_pairs = required_pairs - found_pairs
        if not missing_pairs:
            return

        # 4) Some pairs are missing -> raise a validation error
        raise ValidationError(
            self.env._(
                "Student must be signed up in the enrolment company. "
                "Missing %(n)s pair(s)."
            )
            % {"n": len(missing_pairs)}
        )

    # Overridden methods
    # -------------------------------------------------------------------------

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
                record.display_name = self.env._("New enrolment")

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
            name=f"{self._table}__{'search_active_by_dates_index'}",
        )

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        self._ensure_enrolment_data(values_list)
        sanitize_code(values_list, "upper")
        self._ensure_parent_action(values_list)

        self._perform_a_full_enrolment(values_list)

        result = super().create(values_list)

        return result

    def write(self, values):
        """Overridden method 'write'"""

        sanitize_code(values, "upper")
        self._ensure_parent_action(values)

        self._check_that_the_student_is_not_the_template(values)
        self._perform_a_full_enrolment(values)

        result = super().write(values)

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
                "code": default_code(self.env, _CODE_SEQUENCE),
            }
        )

        return parent.copy(default)

    # Public methods
    # -------------------------------------------------------------------------

    def go_to_student(self):
        student_set = self.mapped("student_id")

        if not student_set:
            msg = self.env._("There are no students")
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
                        "name": self.env._("Students"),
                        "view_mode": "list",
                        "res_id": None,
                        "view_type": "form",
                    }
                )

            return view_act

    # Copy enrolments to another training action
    # -------------------------------------------------------------------------

    def copy_to(self, action_set, new_values=None, existing="skip"):
        """Copy current enrolments into other training actions.

        Each enrolment in ``self`` is copied to every action in
        ``action_set`` by creating or updating a matching enrolment for
        the same student in the target action. The time interval must
        fit inside the target action date range; otherwise a validation
        error is raised.

        Behaviour when an overlapping enrolment already exists for the
        same (student, training_action_id) pair is controlled by
        ``existing``:

        * ``"skip"`` (default): keep the existing enrolment and do not
          create or update anything.
        * ``"replace"``: delete the existing enrolment and create a new
          one with the cloned values.
        * ``"update"``: update the existing enrolment with the cloned
          values and ``new_values`` instead of creating a new one.
        * ``"upgrade"``: like ``"update"``, but the resulting interval
          expands to cover both ranges:

            * ``register`` becomes the minimum of both starts.
            * ``deregister`` becomes the maximum of both ends, treating
              ``False`` (no end) as infinity.

        Args:
            action_set (mixed): Target actions to receive copies. Can be
                a recordset, an id or an iterable of ids; it is
                normalized with :func:`ensure_recordset`.
            new_values (dict | None): Optional overrides to apply to
                each created/updated enrolment.
            existing (str): Conflict policy when an overlapping
                enrolment already exists. One of ``"skip"``,
                ``"replace"``, ``"update"`` or ``"upgrade"``.

        Returns:
            recordset: All created or updated enrolments.
        """

        enrolment_obj = self.env[self._name]
        if not self:
            return enrolment_obj.browse()

        self._ensure_existing_policy(existing)

        action_model = "academy.training.action"
        action_set = ensure_recordset(self.env, action_set, action_model)
        if not action_set:
            return enrolment_obj.browse()

        overrides = dict(new_values or {})
        result_set = enrolment_obj.browse()
        existing_policy = existing

        for enrolment in self:
            base_values = enrolment.copy_data()[0]
            base_values.update(overrides)

            register = base_values.get("register")
            register = fields.Datetime.to_datetime(register)
            deregister = base_values.get("deregister")
            if deregister:
                deregister = fields.Datetime.to_datetime(deregister)

            for action in action_set:
                action_start = action.date_start
                action_stop = action.date_stop

                self._assert_within_window(
                    register, deregister, action_start, action_stop
                )

                values = dict(base_values)
                values["training_action_id"] = action.id

                # Search for overlapping enrolments of the same student
                student_id = enrolment.student_id.id
                if not student_id:
                    continue

                ubound = deregister or datetime.max
                domain = [
                    ("id", "!=", enrolment.id),
                    ("student_id", "=", student_id),
                    ("training_action_id", "=", action.id),
                    ("register", "<", ubound),
                    "|",
                    ("deregister", "=", False),
                    ("deregister", ">", register),
                ]

                existing_enrol = enrolment_obj.search(domain, limit=1)
                if not existing_enrol:
                    new_enrol = enrolment_obj.create(values)
                    result_set |= new_enrol
                    continue

                # Conflict resolution according to the policy
                if existing_policy == "skip":
                    continue

                if existing_policy == "replace":
                    existing_enrol.unlink()
                    new_enrol = enrolment_obj.create(values)
                    result_set |= new_enrol
                    continue

                # update / upgrade -> write into the existing record
                if existing_policy == "upgrade":
                    # Extend interval to cover both enrolments
                    existing_reg = existing_enrol.register
                    existing_der = existing_enrol.deregister

                    if existing_reg and register:
                        values["register"] = min(existing_reg, register)

                    if existing_der is None or deregister is None:
                        values["deregister"] = None
                    else:
                        values["deregister"] = max(existing_der, deregister)

                existing_enrol.write(values)
                result_set |= existing_enrol

        return result_set

    @api.model
    def _ensure_existing_policy(self, existing):
        allowed_policies = {"skip", "replace", "update", "upgrade"}
        if existing not in allowed_policies:
            raise ValidationError(
                self.env._(
                    "Invalid existing policy '%(policy)s'. Allowed values "
                    "are: %(values)s."
                )
                % {
                    "policy": existing,
                    "values": ", ".join(sorted(allowed_policies)),
                }
            )

    def _assert_within_window(
        self, register, deregister, date_start, date_stop
    ):
        """Ensure enrolment dates stay within the action date window."""
        if register < date_start:
            raise ValidationError(
                self.env._(
                    "Registration date cannot be earlier than the "
                    "action start date."
                )
            )

        if (deregister or datetime.max) > (date_stop or datetime.max):
            raise ValidationError(
                self.env._(
                    "Deregistration date cannot be later than the "
                    "action end date."
                )
            )

    # -------------------------------------------------------------------------

    def fetch_enrolments(
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

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def get_timezone(self):
        self.ensure_one()

        company = self.company_id or self.training_action_id.company_id
        if company and company.partner_id and company.partner_id.tz:
            return timezone(company.partner_id.tz)

        return timezone("utc")

    # Auxiliary methods
    # -------------------------------------------------------------------------

    @api.model
    def _ensure_parent_action(self, values_list):
        """Ensure each value dict includes its parent training action.

        When creating enrolments, this method automatically assigns
        the `parent_action_id` based on the `training_action_id`.
        """
        if isinstance(values_list, dict):
            values_list = [values_list]

        # Collect all referenced training_action_id values
        action_ids = set()
        for values in values_list:
            action_id = values.get("training_action_id")
            if isinstance(action_id, models.BaseModel):
                action_id = action_id.id
            if action_id:
                action_ids.add(action_id)

        if not action_ids:
            return

        action_obj = self.env["academy.training.action"]
        action_set = action_obj.browse(action_ids)

        # Map each training action to its parent action
        parent_map = {
            action.id: action.parent_id.id if action.parent_id else action.id
            for action in action_set
        }

        # Apply parent_action_id to values dicts where applicable
        for values in values_list:
            action_id = values.get("training_action_id")
            if isinstance(action_id, models.BaseModel):
                action_id = action_id.id
            parent_id = parent_map.get(action_id)
            if parent_id:
                values["parent_action_id"] = parent_id

    def _check_that_the_student_is_not_the_template(self, values):
        """When registrations are duplicated, the temporary student is
        assigned to them. This method generates a validation error when one of
        them tries to be modified without establishing a real student for it.
        """

        msg = self.env._(
            "You must assign a real student to each of the enrolments."
        )

        temp_student_xid = "academy_base.academy_student_default_template"
        temp_student = self.env.ref(temp_student_xid)

        if temp_student.id in self.student_id.ids:
            new_student_id = values.get("student_id", False)
            if not new_student_id or new_student_id == temp_student.id:
                raise ValidationError(msg)

    @api.model
    def remove_temporary_student_enrolments(self):
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

        _logger.info(
            "Temporary student enrolments will be removed: %d",
            len(enrolment_set),
        )
        enrolment_set.unlink()

    def _perform_a_full_enrolment(self, values):
        """Ensure the M2M of action lines is populated when full_enrolment is
        True. Accepts either a dict (write) or a list of dicts (create).
        """
        values_list = values if isinstance(values, list) else [values]
        for vals in values_list:
            # Only act when explicitly requested or, on write, when the record
            # has the flag
            flag = vals.get("full_enrolment")
            if flag is None and self:
                flag = self[:1].full_enrolment
            if not flag:
                continue

            action_id = vals.get("training_action_id")
            if not action_id and self:
                # during write, allow using the current action
                action_id = self[:1].training_action_id.id

            if action_id:
                action = self.env["academy.training.action"].browse(action_id)
                if action and action.action_line_ids:
                    vals["action_line_ids"] = [
                        (6, 0, action.action_line_ids.ids)
                    ]

    @api.model
    def _ensure_enrolment_date(self, vals_list):
        now = fields.Datetime.now()
        for values in vals_list:
            if not values.get("enrolment_date"):
                values["enrolment_date"] = now

    @api.model
    def _ensure_enrolment_data(self, values_list):
        """Ensure code and enrolment_date are set for the enrolment."""

        for values in values_list:
            if not values.get("code"):
                values["code"] = default_code(self.env, _CODE_SEQUENCE)

            if not values.get("enrolment_date"):
                self._ensure_enrolment_date([values])

    # Maintenance tasks
    # -------------------------------------------------------------------------

    def full_enrolment_maintenance_task(self):
        """Synchronize action lines for full enrolment records.

        This method is intended to be called from a scheduled maintenance
        job. It processes all active enrolments marked with
        ``full_enrolment = True`` and makes sure their ``action_line_ids``
        match the active action lines of the related training action.

        The synchronization is done in two steps:

        * :meth:`_fem_task_with_orm` computes which lines must be unlinked
          and which ones must be appended for each enrolment.
        * :meth:`_fem_task_optimized_m2m_update` applies the corresponding
          batched M2M updates to minimize the number of writes.

        The method is idempotent and does not return any value.
        """

        to_unlink, to_append = self._fem_task_with_orm()
        self._fem_task_optimized_m2m_update(to_unlink, 3)
        self._fem_task_optimized_m2m_update(to_append, 4)

    def _fem_task_with_orm(self):
        """Compute M2M diffs for full enrolment action lines."""

        enrolment_obj = self.with_context(active_test=False)

        now = fields.Datetime.now()

        # 1) Candidate enrolments
        enrolment_domain = [
            ("full_enrolment", "=", True),
            ("active", "=", True),
            "|",
            ("deregister", "=", False),
            ("deregister", ">=", now),
        ]
        enrolment_set = enrolment_obj.search(enrolment_domain)
        if not enrolment_set:
            return {}, {}

        # 2) Involved training actions
        action_set = enrolment_set.mapped("training_action_id")

        # 3) Map action -> active lines that each enrolment should have
        lines_by_action = {}
        for action in action_set:
            lines_by_action.setdefault(action.id, set())

            line_set = action.action_line_ids
            if not line_set:
                continue

            filtered_set = line_set.filtered(lambda line: line.active)
            if not filtered_set:
                continue

            lines_by_action[action.id].update(filtered_set.ids)

        # 4) Recorrer enrolments y calcular diferencias
        to_unlink = {}
        to_append = {}

        for enrolment in enrolment_set:
            action_id = enrolment.training_action_id.id
            should_have = lines_by_action.get(action_id, set())

            # All currently linked lines (active or archived)
            current_lines = set(enrolment.action_line_ids.ids)

            missing = should_have - current_lines  # → to_append
            extra = current_lines - should_have  # → to_unlink

            if missing:
                to_append[enrolment.id] = list(missing)
            if extra:
                to_unlink[enrolment.id] = list(extra)

        return to_unlink, to_append

    @staticmethod
    def _fem_task_split_by_m2m_op(query_result):
        """Split SQL result rows into unlink/append maps."""

        to_unlink = {}
        to_append = {}
        for row in query_result:
            enrolment_id = row.get("enrolment_id", False)
            action_line_id = row.get("action_line_id", False)
            if not enrolment_id or not action_line_id:
                continue

            if row.get("to_unlink", False):
                to_unlink.setdefault(enrolment_id, [])
                to_unlink[enrolment_id].append(action_line_id)
            elif row.get("to_append", False):
                to_append.setdefault(enrolment_id, [])
                to_append[enrolment_id].append(action_line_id)

        return to_unlink, to_append

    @api.model
    def _fem_task_optimized_m2m_update(self, enrol_line_map, op_num):
        """Apply grouped M2M updates on action_line_ids."""

        to_execute_grouped = {}
        for enrolment_id, action_line_ids in enrol_line_map.items():
            action_line_array = tuple(sorted(action_line_ids))
            to_execute_grouped.setdefault(action_line_array, [])
            to_execute_grouped[action_line_array].append(enrolment_id)

        enrolment_obj = self.env[self._name]
        for action_line_array, enrolment_ids in to_execute_grouped.items():
            enrolment_set = enrolment_obj.browse(enrolment_ids)
            if not enrolment_set:
                continue
            m2m_ops = [(op_num, line_id, 0) for line_id in action_line_array]
            enrolment_set.write({"action_line_ids": m2m_ops})
