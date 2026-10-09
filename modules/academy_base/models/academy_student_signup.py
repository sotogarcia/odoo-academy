###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from logging import getLogger

from odoo import api, fields, models
from odoo.addons.academy_base.utils.helpers import (
    one2many_count,
    one2many_count_search_domain,
)
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

from ..utils.datetime_utils import DATETIME_POSITIVE_INFINITY as INFINITY
from ..utils.record_utils import prevent_field_changes

_logger = getLogger(__name__)


class AcademyStudentSignup(models.Model):
    """Per-company sign-up data for students."""

    _name = "academy.student.signup"
    _description = "Per-company sign-up data for academy students"

    _rec_name = "id"
    _order = "company_id, id"

    _inherit = ["mail.thread"]  # noqa: RUF012

    _check_company_auto = True

    company_id = fields.Many2one(
        string="Company",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.env.company,
        help="Company this sign-up data applies to.",
        comodel_name="res.company",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
        tracking=True,
        copy=True,
    )

    student_id = fields.Many2one(
        string="Student",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Student this sign-up data belongs to.",
        comodel_name="academy.student",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
        copy=True,
    )

    signup_code = fields.Char(
        string="Sign-up code",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
        help="Unique code assigned when the student signs up at the centre.",
        size=50,
        translate=False,
        tracking=True,
        copy=False,
    )

    signup_date = fields.Datetime(
        string="Sign-up date",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: fields.Datetime.now(),
        help="Date and time when the student signed up at the centre.",
        tracking=True,
        copy=False,
    )

    transition_ids = fields.One2many(
        string="State transitions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="State transitions associated with this student sign-up.",
        comodel_name="academy.student.signup.state.transition",
        inverse_name="signup_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    state = fields.Selection(
        string="State",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Current state of the student sign-up.",
        compute="_compute_state",
        store=False,
        selection=[
            ("signed_up", "Signed up"),
            ("enrolled", "Enrolled"),
        ],
    )

    @api.depends(
        "transition_ids",
        "transition_ids.timestamp",
        "transition_ids.state",
    )
    def _compute_state(self):
        now = fields.Datetime.now()

        transition_obj = self.env["academy.student.signup.state.transition"]

        domain = [("signup_id", "in", self.ids), ("timestamp", "<=", now)]
        order = "signup_id, timestamp DESC, id DESC"
        transitions = transition_obj.search(domain, order=order)

        states = {}
        for transition in transitions:
            signup_id = transition.signup_id.id
            states.setdefault(signup_id, transition.state)

        for signup in self:
            signup.state = states.get(signup.id, "signed_up")

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

    enrolment_ids = fields.One2many(
        string="Enrolments",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Enrolments associated with this student sign-up.",
        comodel_name="academy.training.action.enrolment",
        inverse_name="signup_id",
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
        help="Number of active enrolments associated with this sign-up.",
        compute="_compute_enrolment_count",
        search="_search_enrolment_count",
    )

    enrolment_count_str = fields.Char(
        string="Enrolment summary",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Number of current enrolments / total number of active enrolments.",
        translate=False,
        compute="_compute_enrolment_count",
    )

    @api.depends(
        "enrolment_ids",
        "enrolment_ids.active",
        "enrolment_ids.register",
        "enrolment_ids.deregister",
    )
    def _compute_enrolment_count(self):
        totals = one2many_count(self, "enrolment_ids")

        domain = [("is_current", "=", True)]
        currents = one2many_count(self, "enrolment_ids", domain)

        for signup in self:
            total_count = totals.get(signup.id, 0)
            signup.enrolment_count = total_count

            current_count = currents.get(signup.id, 0)
            signup.enrolment_count_str = (
                f"{current_count: >3} / {total_count: <3}"
            )

    @api.model
    def _search_enrolment_count(self, operator, value):
        return one2many_count_search_domain(
            self,
            "enrolment_ids",
            operator,
            value,
        )

    latest_enrolment_end = fields.Datetime(
        string="End of training",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Latest effective enrolment end.",
        compute="_compute_latest_enrolment_end",
        store=True,
    )

    @api.depends(
        "enrolment_ids",
        "enrolment_ids.available_until",
        "enrolment_ids.active",
        "company_id.include_archived",
    )
    def _compute_latest_enrolment_end(self):
        enrolment_obj = self.env["academy.training.action.enrolment"]

        context = dict(self.env.context, active_test=False)
        enrolment_obj = enrolment_obj.with_context(context).sudo()

        domain = [
            ("signup_id", "in", self.ids),
            "|",
            ("signup_id.company_id.include_archived", "=", True),
            ("active", "=", True),
        ]

        rows = enrolment_obj.read_group(
            domain=domain,
            fields=["available_until:max"],
            groupby=["signup_id"],
            lazy=False,
        )

        latest_end = {
            row["signup_id"][0]: row.get("available_until")
            for row in rows
            if row.get("signup_id")
        }

        for signup in self:
            signup.latest_enrolment_end = latest_end.get(signup.id, False)

    # -- Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "unique_student_company",
            "UNIQUE(student_id, company_id)",
            "There is already sign-up data for this student and company.",
        ),
        (
            "uniq_code_company",
            "UNIQUE(company_id, signup_code)",
            "Sign-up code must be unique per company.",
        ),
    ]

    # -- Signup sequence methods
    # -------------------------------------------------------------------------

    @api.model
    def _ensure_signup_date(self, vals_list):
        today = fields.Datetime.now()
        for values in vals_list:
            if not values.get("signup_date"):
                values["signup_date"] = today

    @api.model
    def _next_signup_code(self, company_id):
        """Return next sign-up code using company-specific sequence,
        falling back to a known default XMLID."""
        sequence_obj = self.env["ir.sequence"].with_company(company_id)

        # 1) Try company-specific sequence (same code, bound to company)
        signup_code = "academy.student.signup.sequence"
        sequence_domain = [
            ("code", "=", signup_code),
            ("company_id", "=", company_id),
        ]
        sequence = sequence_obj.search(sequence_domain, limit=1)
        if sequence:
            return sequence.with_company(company_id).next_by_id()

        # 2) Explicit fallback to the known default sequence XMLID
        sequence_xid = "academy_base.ir_sequence_academy_student_signup"
        fallback = self.env.ref(sequence_xid, raise_if_not_found=False)
        if fallback:
            return fallback.with_company(company_id).next_by_id()

        # 3) Last resort: let Odoo try any global sequence with that code
        code = sequence_obj.next_by_code(signup_code)
        if code:
            _logger.warning(
                "Using global sequence by code for company_id=%s", company_id
            )
            return code

        raise UserError(
            _(
                "Missing sequence for student sign-up. "
                "Create a company-specific sequence with code %(code)s "
                "or define the fallback %(xid)s."
            )
            % {
                "code": signup_code,
                "xid": sequence_xid,
            }
        )

    @api.model
    def _ensure_signup_data(self, values):
        i18n_new = _("New")

        if values.get("signup_code", i18n_new) == i18n_new:
            company_id = values.get("company_id") or self.env.company.id
            values["signup_code"] = self._next_signup_code(company_id)

        if not values.get("signup_date", False):
            values["signup_date"] = fields.Datetime.now()

    def _assert_no_enrolments_before_unlink(self):
        """Raise ValidationError if any sign-up has related enrolments."""

        signups = self.with_context(active_test=False)

        if signups.filtered("enrolment_ids"):
            message = self.env._(
                "Cannot remove sign-up records because there are enrolments "
                "for at least one sign-up in this batch."
            )

            raise ValidationError(message)

    # -- Overriden methods
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        for values in values_list:
            self._ensure_signup_data(values)

        result = super().create(values_list)

        return result

    def write(self, values):
        """Overridden 'write' method.
        Prevents the user or company from being changed.
        """

        fields_to_freeze = ("student_id", "company_id")
        prevent_field_changes(self, values, fields_to_freeze)

        return super().write(values)

    def unlink(self):
        self._assert_no_enrolments_before_unlink()

        return super().unlink()

    def copy(self, default=None):
        self.ensure_one()

        default = dict(default or {})
        self._check_copy_target(default)

        return super().copy(default)

    @api.depends(
        "signup_code",
        "student_id",
        "student_id.name",
        "company_id",
        "company_id.name",
    )
    @api.depends_context("lang", "signup_short_display_name")
    def _compute_display_name(self):
        na = self.env._("#N/A")

        short = self.env.context.get("signup_short_display_name", False)
        method_name = (
            "_compute_short_display_name"
            if short
            else "_compute_long_display_name"
        )

        for record in self:
            compute_method = getattr(record, method_name)
            record.display_name = compute_method(na)

    def _compute_long_display_name(self, na):
        self.ensure_one()

        pattern = self.env._("{code} — {student} / {company}")
        components = {"code": na, "student": na, "company": na}

        if self.signup_code:
            components["code"] = self.signup_code

        if self.student_id and self.student_id.display_name:
            components["student"] = self.student_id.name

        if self.company_id and self.company_id.display_name:
            components["company"] = self.company_id.name

        return pattern.format(**components)

    def _compute_short_display_name(self, na):
        return self.signup_code or na

    def _check_copy_target(self, default):
        """Validate that a copied sign-up targets another student or company.

        The copied record must differ from the original sign-up in at least one
        component of its functional identity: `student_id` or `company_id`.

        :param dict default: Values supplied to `copy()` for the new record.
        :raises UserError: If both student and company remain unchanged.
        """
        self.ensure_one()

        company_id = default.get("company_id", self.company_id.id)
        student_id = default.get("student_id", self.student_id.id)

        if (
            company_id == self.company_id.id
            and student_id == self.student_id.id
        ):
            raise UserError(
                _("Duplication is only allowed for a new student or company.")
            )

    # -- State transition management ---------------------------------------------

    def _get_enrolments_by_signup(self):
        """Return active enrolments indexed by sign-up."""

        enrolment_obj = self.env["academy.training.action.enrolment"]

        indexed = {signup.id: enrolment_obj.browse() for signup in self}

        if not self:
            return indexed

        domain = [
            ("signup_id", "in", self.ids),
            ("active", "=", True),
        ]
        enrolments = enrolment_obj.search(domain)

        for enrolment in enrolments:
            indexed[enrolment.signup_id.id] |= enrolment

        return indexed

    def _filter_relevant_enrolments(self, enrolment_set):
        """Keep only enrolments belonging to the current sign-ups."""

        if not self or not enrolment_set:
            return self.env["academy.training.action.enrolment"].browse()

        return enrolment_set.filtered_domain([("signup_id", "in", self.ids)])

    def _filter_relevant_transitions(self, transition_set):
        """Keep only transitions belonging to the current sign-ups."""

        if not self or not transition_set:
            return self.env["academy.student.signup.state.transition"].browse()

        return transition_set.filtered_domain([("signup_id", "in", self.ids)])

    @staticmethod
    def _enrolment_sort_key(enrolment):
        """Return the chronological sort key for an enrolment."""

        return (enrolment.register, enrolment.id)

    @staticmethod
    def _closing_enrolment(enrolment):
        return enrolment if enrolment.deregister else False

    @staticmethod
    def _has_closing_tie_priority(
        enrolment_end,
        component_end,
        closing_enrolment,
        enrolment,
    ):
        return (
            enrolment_end == component_end
            and closing_enrolment
            and enrolment.id < closing_enrolment.id
        )

    def _split_enrolment_components(self, enrolment_set):
        """Split enrolments into temporally connected components.

        Two enrolments belong to the same component when their time intervals
        overlap or touch. If there is a gap between them, they belong to separate
        components.

        An enrolment without `deregister` is considered open-ended up to
        `INFINITY`, so any later enrolment remains connected to the same component.

        Each component is returned as a tuple with the following structure:

            (
                component_enrolments,
                start_enrolment,
                closing_enrolment,
            )

        `component_enrolments` contains all enrolments in the component.

        `start_enrolment` is the enrolment that determines the beginning of the
        component.

        `closing_enrolment` is the enrolment that determines the end of the
        component, or `False` when the component is open-ended.

        Example:

            A: 01 ───── 10
            B:      05 ───── 15
            C:                   20 ── 25

        Result:

            ([A, B], A, B)
            ([C], C, C)
        """

        self.ensure_one()

        if not enrolment_set:
            return []

        enrolment_set = enrolment_set.sorted(key=self._enrolment_sort_key)

        components = []

        component = enrolment_set.browse()
        start_enrolment = False
        closing_enrolment = False
        component_end = None

        for enrolment in enrolment_set:
            enrolment_end = enrolment.deregister or INFINITY

            if not component:
                component = enrolment
                start_enrolment = enrolment
                closing_enrolment = self._closing_enrolment(enrolment)
                component_end = enrolment_end
                continue

            disconnected = enrolment.register > component_end

            if disconnected:
                new_component = (component, start_enrolment, closing_enrolment)
                components.append(new_component)

                component = enrolment
                start_enrolment = enrolment
                closing_enrolment = self._closing_enrolment(enrolment)
                component_end = enrolment_end
                continue

            component |= enrolment

            if not enrolment.deregister:
                component_end = INFINITY
                closing_enrolment = False
            elif enrolment_end > component_end:
                component_end = enrolment_end
                closing_enrolment = enrolment
            elif self._has_closing_tie_priority(
                enrolment_end,
                component_end,
                closing_enrolment,
                enrolment,
            ):
                closing_enrolment = enrolment

        if component:
            new_component = (component, start_enrolment, closing_enrolment)
            components.append(new_component)

        return components

    def _select_enrolment_components(self, components, enrolment_set):
        """Return components intersecting the given enrolments."""

        self.ensure_one()

        selected_components = []
        selected_enrolments = enrolment_set.browse()

        for component in components:
            component_enrolments, _, _ = component

            if enrolment_set & component_enrolments:
                selected_components.append(component)
                selected_enrolments |= component_enrolments

        return selected_components, selected_enrolments

    def get_state_transition_scope(self, enrolment_set):
        """Return the enrolment scope affected by a transition change.

        This method must be called before modifying or deleting existing
        enrolments when a partial state-transition synchronization will be
        performed later.

        The returned recordset preserves the currently affected temporal
        components so it can be passed to `synchronize_state_transitions()`
        after the change.
        """

        signup_set = self.exists()
        enrolment_set = enrolment_set.exists()

        if not signup_set:
            return enrolment_set.browse()

        if not enrolment_set:
            return enrolment_set

        enrolment_set = signup_set._filter_relevant_enrolments(enrolment_set)
        if not enrolment_set:
            return enrolment_set

        active_enrolment_set = enrolment_set.filtered("active")
        if not active_enrolment_set:
            return enrolment_set

        by_signup = signup_set._get_enrolments_by_signup()
        scope = enrolment_set

        for signup in signup_set:
            seeds = signup._filter_relevant_enrolments(active_enrolment_set)

            if not seeds:
                continue

            enrolments = by_signup[signup.id]
            components = signup._split_enrolment_components(enrolments)

            _, connected_enrolments = signup._select_enrolment_components(
                components,
                seeds,
            )

            scope |= connected_enrolments

        return scope

    def _get_transition_scope(self, enrolments, existing, restrict_to=None):
        """Return components and existing transitions within the sync scope."""

        self.ensure_one()

        signup_existing = self._filter_relevant_transitions(existing)

        if restrict_to is None:
            components = self._split_enrolment_components(enrolments)
            return components, signup_existing

        seeds = self._filter_relevant_enrolments(restrict_to)

        if not seeds:
            return [], signup_existing.browse()

        active_seeds = seeds & enrolments

        if not active_seeds:
            domain = [("enrolment_id", "in", seeds.ids)]
            signup_existing = signup_existing.filtered_domain(domain)

            return [], signup_existing

        components = self._split_enrolment_components(enrolments)

        selected_components, current_scope = self._select_enrolment_components(
            components,
            active_seeds,
        )

        affected = seeds | current_scope

        domain = [("enrolment_id", "in", affected.ids)]
        signup_existing = signup_existing.filtered_domain(domain)

        return selected_components, signup_existing

    def _prepare_component_transitions(self, component):
        """Return expected transition values for an enrolment component."""

        self.ensure_one()

        _, start_enrolment, closing_enrolment = component

        transitions = {}

        key = ("enrolled", start_enrolment.id)
        transitions[key] = {
            "signup_id": self.id,
            "state": "enrolled",
            "enrolment_id": start_enrolment.id,
        }

        if not closing_enrolment:
            return transitions

        key = ("signed_up", closing_enrolment.id)
        transitions[key] = {
            "signup_id": self.id,
            "state": "signed_up",
            "enrolment_id": closing_enrolment.id,
        }

        return transitions

    def _compare_existing_transitions(self, existing, expected):
        """Return obsolete transitions and keys already present."""

        obsolete = existing.browse()
        existing_keys = set()

        for transition in existing:
            key = (transition.state, transition.enrolment_id.id)

            if key not in expected:
                obsolete |= transition
                continue

            existing_keys.add(key)

        return obsolete, existing_keys

    def synchronize_state_transitions(self, enrolment_set=None):
        """Synchronize state transitions with the current enrolment periods.

        When `enrolment_set` is omitted, all transitions for the current
        sign-ups are synchronized.

        For a partial synchronization after updating or deleting existing
        enrolments, `enrolment_set` must be the scope previously returned by
        `get_state_transition_scope()` before the change was applied.
        """

        signup_set = self.exists()
        transition_obj = self.env["academy.student.signup.state.transition"]

        if not signup_set:
            return True

        restrict_to = None

        if enrolment_set is not None:
            restrict_to = enrolment_set.exists()
            restrict_to = signup_set._filter_relevant_enrolments(restrict_to)

        by_signup = signup_set._get_enrolments_by_signup()

        domain = [
            ("signup_id", "in", signup_set.ids),
            ("enrolment_id", "!=", False),
        ]
        existing = transition_obj.search(domain)

        to_unlink = transition_obj.browse()
        values_list = []

        for signup in signup_set:
            enrolments = by_signup[signup.id]

            components, signup_existing = signup._get_transition_scope(
                enrolments,
                existing,
                restrict_to=restrict_to,
            )

            expected = {}

            for component in components:
                values = signup._prepare_component_transitions(component)
                expected.update(values)

            obsolete, existing_keys = signup._compare_existing_transitions(
                signup_existing,
                expected,
            )

            to_unlink |= obsolete

            for key, values in expected.items():
                if key not in existing_keys:
                    values_list.append(values)

        if to_unlink:
            to_unlink.unlink()

        if values_list:
            transition_obj.create(values_list)

        return True
