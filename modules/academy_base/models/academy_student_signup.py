###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from logging import getLogger

from odoo import api, fields, models
from odoo.addons.academy_base.utils.helpers import (
    build_act_window_action,
    one2many_count,
    one2many_count_search_domain,
)
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import AND
from odoo.tools import SQL
from odoo.tools.translate import _

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
        required=True,
        readonly=True,
        index=True,
        default="signed_up",
        help="Current state of the student sign-up.",
        copy=False,
        selection=[
            ("signed_up", "Signed up"),
            ("enrolled", "Enrolled"),
        ],
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
    )
    def _compute_latest_enrolment_end(self):
        enrolment_obj = self.env["academy.training.action.enrolment"].sudo()

        domain = [
            ("signup_id", "in", self.ids),
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

    @api.constrains("signup_date")
    def _check_enrolment_register_dates(self):
        self.validate_enrolment_register_dates()

    def _get_first_enrolment_register_by_signup(self):
        enrolment_obj = self.env["academy.training.action.enrolment"]
        enrolment_obj = enrolment_obj.with_context(active_test=False)

        results = enrolment_obj.read_group(
            domain=[("signup_id", "in", self.ids)],
            fields=["signup_id", "first_register:min(register)"],
            groupby=["signup_id"],
            lazy=False,
        )

        first_register_by_signup = {
            result["signup_id"][0]: result["first_register"]
            for result in results
        }

        return first_register_by_signup

    def validate_enrolment_register_dates(self):
        """Ensure sign-up dates do not follow their first enrolment."""
        first_by_signup = self._get_first_enrolment_register_by_signup()

        for signup in self:
            first_register = first_by_signup.get(signup.id)

            if first_register and signup.signup_date > first_register:
                pattern = _(
                    "The sign-up date (%s) cannot be later than the first "
                    "enrolment registration date (%s)."
                )
                raise ValidationError(
                    pattern
                    % (
                        fields.Datetime.to_string(signup.signup_date),
                        fields.Datetime.to_string(first_register),
                    )
                )

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

    def lock_signups_for_concurrency(self):
        # Lock sign-ups to prevent concurrent state transitions.
        sql = """
            SELECT id
            FROM academy_student_signup
            WHERE id = ANY(%s)
            ORDER BY id
            FOR UPDATE
        """
        self.env.cr.execute(sql, (self.ids,))

    def _build_signup_state_base_dictionary(self):
        """Return the initial data structure for state resolution.

        Contains historical information, academic coverage data,
        and the results produced by the state rule chain.

        Dependent modules may extend this dictionary with additional
        data required by their own state resolution rules.

        Returns:
            dict: Initial state calculation and transition data.
        """
        return {
            "transition_id": False,
            "previous_state": False,
            "timestamp": False,
            "current_midnight_utc": False,
            "first_register": False,
            "last_available_until": False,
            "enrolment_count": 0,
            "state": False,
            "transitions": [],
        }

    def _get_latest_transition_data(self):
        """Return the latest recorded state transition for each sign-up.

        Selects the transition with the greatest timestamp, using the
        greatest ID to resolve ties. Only one transition is returned
        per sign-up.

        Returns:
            dict: Mapping of sign-up IDs to their latest transition data.

            {
                signup_id: {
                    "signup_id": int,
                    "transition_id": int,
                    "previous_state": str,
                    "timestamp": datetime,
                },
                ...
            }

            Sign-ups without recorded transitions are omitted.
        """

        if not self:
            return {}

        sql = """
            SELECT DISTINCT ON (signup_id)
                signup_id,
                "id" AS transition_id,
                "state" AS previous_state,
                "timestamp"
            FROM academy_student_signup_state_transition
            WHERE signup_id = ANY(%s)
            ORDER BY signup_id, "timestamp" DESC, "id" DESC
        """

        self.env.cr.execute(sql, (self.ids,))

        transition_data = {
            row["signup_id"]: row for row in self.env.cr.dictfetchall()
        }

        return transition_data

    def _get_effective_enrolments(self, start_utc, end_utc):
        """Return effective enrolment coverage data grouped by sign-up.

        Selects active enrolments whose effective period intersects
        the supplied UTC interval, representing the company's current
        local calendar day.

        The start and end dates are inclusive at the calendar-day level.
        Enrolments starting or ending today therefore provide coverage
        throughout the applicable day.

        Archived enrolments are explicitly excluded, regardless of
        the active_test context.

        Args:
            start_utc (datetime): Inclusive UTC beginning of the
                company's current local day.
            end_utc (datetime): Exclusive UTC beginning of the
                following local day.

        Returns:
            dict: Mapping of sign-up IDs to aggregated enrolment data.

                {
                    signup_id: {
                        "first_register": datetime | False,
                        "last_available_until": datetime | False,
                        "enrolment_count": int,
                    },
                    ...
                }

            Sign-ups without effective enrolments are omitted.
        """
        if not self:
            return {}

        enrolment_obj = self.env["academy.training.action.enrolment"]

        rows = enrolment_obj.read_group(
            domain=[
                ("signup_id", "in", self.ids),
                ("active", "=", True),
                ("register", "<", end_utc),
                ("available_until", ">=", start_utc),
            ],
            fields=[
                "first_register:min(register)",
                "last_available_until:max(available_until)",
                "enrolment_count:count(id)",
            ],
            groupby=["signup_id"],
            lazy=False,
        )

        return {
            row["signup_id"][0]: {
                "first_register": row["first_register"],
                "last_available_until": row["last_available_until"],
                "enrolment_count": row["enrolment_count"],
            }
            for row in rows
        }

    def _get_signup_state_data_by_company(self, company, state_data):
        start_utc, end_utc = company.local_day_bounds_to_utc()

        for signup in self:
            state_data[signup.id]["current_midnight_utc"] = start_utc

        enrolment_data = self._get_effective_enrolments(start_utc, end_utc)

        for signup_id, values in enrolment_data.items():
            state_data[signup_id].update(values)

    def _get_signup_state_data(self):
        """Collect the data required to resolve sign-up states and transitions.

        Builds a dictionary indexed by sign-up ID, combining the latest
        recorded transition with academic coverage data evaluated
        according to each company's current local day.

        The collected data is intended for subsequent rule evaluation.
        This method does not resolve states, select transition sources,
        or generate transition records.

        Returns:
            dict: State calculation data indexed by sign-up ID.
        """
        state_data = {
            signup.id: self._build_signup_state_base_dictionary()
            for signup in self
        }

        transition_data = self._get_latest_transition_data()

        for signup_id, values in transition_data.items():
            state_data[signup_id].update(values)

        for company in self.company_id:
            signups = self.filtered(
                lambda signup: signup.company_id == company  # noqa: B023
            )

            signups._get_signup_state_data_by_company(company, state_data)

        return state_data

    def _rule_signup_enrolled(self, data):
        """Resolve the sign-up state when academic coverage exists.

        Returns the enrolled state and prepares a transition when
        the last recorded state differs from enrolled.

        The source document is left pending for subsequent resolution.

        Args:
            data (dict): State calculation data for this sign-up.

        Returns:
            dict | None: Resolved state and transitions, or None
                when no effective enrolment exists.
        """
        if not data["enrolment_count"]:
            return None

        transitions = []

        if not data["transition_id"] or data["previous_state"] != "enrolled":
            transitions.append(
                {
                    "state": "enrolled",
                    "source_ref": None,
                }
            )

        return {
            "state": "enrolled",
            "transitions": transitions,
        }

    def _rule_signup_default(self, data):
        """Resolve the default sign-up state.

        Returns signed_up when no preceding rule applies.
        A transition is prepared only when the last recorded
        state differs from signed_up.

        The initial transition is handled separately by the
        synchronization process.

        Args:
            data (dict): State calculation data for this sign-up.

        Returns:
            dict: Resolved state and ordered transitions.
        """
        transitions = []

        if data["transition_id"] and data["previous_state"] != "signed_up":
            transitions.append(
                {
                    "state": "signed_up",
                    "source_ref": False,
                }
            )

        return {
            "state": "signed_up",
            "transitions": transitions,
        }

    def _get_signup_state_rules(self):
        """Return the ordered rules for resolving sign-up states.

        Each rule is represented by a priority and the name of its
        evaluator method. Rules are evaluated in ascending priority
        order, stopping at the first applicable result.

        Dependent modules may extend the chain by adding rules
        between the academic coverage rule and the default rule.

        Returns:
            list[tuple[int, str]]: Rule priorities and method names.
        """
        return [
            (10, "_rule_signup_enrolled"),
            (1000, "_rule_signup_default"),
        ]

    def _resolve_signup_state(self, state_data):
        """Resolve the state and transitions using an ordered rule chain.

        Evaluates the available rules in priority order until one
        resolves the sign-up. Each rule returns None when it does
        not apply, or a dictionary containing the resulting state
        and the ordered transition steps.

        The first applicable rule determines the complete result.
        No database records are created or modified.

        Args:
            state_data (dict): State calculation data indexed by
                sign-up ID.

        Returns:
            dict: Updated state data for this sign-up, including
                the resolved state and transition sequence.

        Raises:
            UserError: If no rule can resolve the sign-up state.
        """
        self.ensure_one()

        data = state_data[self.id]
        rules = sorted(self._get_signup_state_rules())

        for _, method_name in rules:  # noqa: F402
            resolver = getattr(self, method_name)
            result = resolver(data)

            if result is not None:
                data["state"] = result["state"]
                data["transitions"] = result["transitions"]
                return data

        err = _("No rule could resolve the sign-up state.")
        raise UserError(err)

    def _resolve_signup_states(self, state_data):
        """Resolve the state and transition sequence for each sign-up.

        Delegates resolution to each sign-up's state rule chain,
        which determines the resulting state and the ordered
        transitions required to reach it.

        Source documents are completed in a subsequent step.
        No database records are created or modified.

        Args:
            state_data (dict): State calculation data indexed by
                sign-up ID, containing historical and coverage data.

        Returns:
            dict: State data enriched with the resolved state and
                its ordered transition sequence.
        """
        for signup in self:
            signup._resolve_signup_state(state_data)

        return state_data

    def _get_enrolment_state_sources(self, start_utc, end_utc, ended=False):
        """Return the most relevant enrolment for each sign-up.

        Selects at most one enrolment per sign-up, according to the
        requested temporal condition:

        - Effective enrolments (ended=False): enrolments whose interval
          overlaps the company's current local day. The enrolment with
          the earliest registration date is selected.
        - Ended enrolments (ended=True): enrolments whose effective end
          precedes the beginning of the company's current local day.
          The enrolment with the latest effective end is selected.

        Only active enrolments belonging to the sign-ups in ``self`` are
        considered. Archived enrolments are explicitly excluded,
        regardless of the ``active_test`` context.

        The temporal boundaries are expressed as naive UTC datetimes,
        following Odoo's datetime convention. The current local day is
        represented by the interval [start_utc, end_utc).

        The query is built using the Odoo ORM to preserve domain
        processing and access rules. PostgreSQL's DISTINCT ON is then
        used to select a single enrolment per sign-up without retrieving
        all matching records.

        Selection order:
            - Effective: register ASC, id ASC.
            - Ended: available_until DESC, id ASC.

        The lowest record ID resolves ties deterministically.

        Args:
            start_utc (datetime): UTC beginning of the company's
                current local day, inclusive.
            end_utc (datetime): UTC beginning of the following local
                day, exclusive.
            ended (bool): Whether to select ended enrolments instead
                of currently effective enrolments. Defaults to False.

        Returns:
            dict[int, academy.training.action.enrolment]:
                Mapping of sign-up IDs to singleton enrolment recordsets.

                Sign-ups without matching enrolments are omitted.
                An empty recordset returns an empty dictionary.

                Example:
                    {
                        signup_id: enrolment_record,
                        ...
                    }
        """

        if not self:
            return {}

        enrolment_obj = self.env["academy.training.action.enrolment"]

        base_domain = [
            ("signup_id", "in", self.ids),
            ("active", "=", True),
        ]

        if ended:
            ended_domain = [("available_until", "<", start_utc)]
            domain = AND([base_domain, ended_domain])
            sort_field = "available_until"
            sort_direction = SQL("DESC")
        else:
            started_domain = [
                ("register", "<", end_utc),
                ("available_until", ">=", start_utc),
            ]
            domain = AND([base_domain, started_domain])
            sort_field = "register"
            sort_direction = SQL("ASC")

        query = enrolment_obj._search(domain)

        table = enrolment_obj._table
        signup_column = SQL.identifier(table, "signup_id")
        id_column = SQL.identifier(table, "id")
        sort_column = SQL.identifier(table, sort_field)

        query.order = SQL(
            "%s ASC, %s %s, %s ASC",
            signup_column,
            sort_column,
            sort_direction,
            id_column,
        )

        sql = query.select(
            SQL(
                "DISTINCT ON (%s) %s, %s",
                signup_column,
                signup_column,
                id_column,
            )
        )

        rows = self.env.execute_query(sql)

        return {
            signup_id: enrolment_obj.browse(enrolment_id)
            for signup_id, enrolment_id in rows
        }

    def _get_signup_state_sources(self, start_utc, end_utc, state_data):
        """Return source documents for states managed by academy_base."""
        signups = self.filtered(
            lambda signup: state_data[signup.id]["state"] == "enrolled"
        )

        return signups._get_enrolment_state_sources(start_utc, end_utc)

    def _fill_signup_state_sources(self, state_data):
        """Fill missing source documents in final planned transitions.

        Processes sign-ups by company and delegates source selection
        to _get_signup_state_sources().

        Only the last planned transition is considered. A source_ref
        of None indicates that its source remains unresolved.

        Updates state_data in place without creating database records.

        Args:
            state_data (dict): State calculation data indexed by sign-up ID.
        """
        for company in self.company_id:
            signups = self.filtered(
                lambda signup: signup.company_id == company  # noqa: B023
            )

            pending = signups.filtered(
                lambda signup: (
                    state_data[signup.id]["transitions"]
                    and state_data[signup.id]["transitions"][-1]["source_ref"]
                    is None
                )
            )

            if not pending:
                continue

            start_utc, end_utc = company.local_day_bounds_to_utc()

            sources = pending._get_signup_state_sources(
                start_utc,
                end_utc,
                state_data,
            )

            for signup in pending:
                transition = state_data[signup.id]["transitions"][-1]
                transition["source_ref"] = sources.get(signup.id, False)

    def _prepare_signup_state_changes(self, state_data):
        timestamp = fields.Datetime.now()
        transition_values = []
        state_updates = {}

        for signup in self:
            data = state_data[signup.id]
            previous_state = data["previous_state"]

            if not data["transition_id"]:
                transition_values.append(
                    {
                        "signup_id": signup.id,
                        "previous_state": False,
                        "state": "signed_up",
                        "timestamp": timestamp,
                        "source_ref": False,
                    }
                )
                previous_state = "signed_up"

            for step in data["transitions"]:
                transition_values.append(
                    {
                        "signup_id": signup.id,
                        "previous_state": previous_state,
                        "state": step["state"],
                        "timestamp": timestamp,
                        "source_ref": step["source_ref"],
                    }
                )
                previous_state = step["state"]

            if previous_state != data["state"]:
                raise ValidationError(
                    _("Resolved transitions do not match the resulting state.")
                )

            if signup.state != data["state"]:
                state_updates.setdefault(data["state"], []).append(signup.id)

        return transition_values, state_updates

    def synchronize_state_transitions(self, enrolment_set=None):
        """Synchronize sign-up states and register their transitions.

        Collects the data required for state resolution, evaluates the
        available rules, and completes the source documents of planned
        transitions before persisting any changes.

        The initial signed_up transition is always recorded when no
        previous history exists. Subsequent transitions are taken from
        the ordered sequence resolved by the rule chain.

        All transitions are created before updating the stored states.
        The transition hook is executed once, after all changes, within
        the same transaction.

        Returns:
            academy.student.signup.state.transition:
                Recordset of newly created transitions.
        """
        transition_obj = self.env["academy.student.signup.state.transition"]

        if not self:
            return transition_obj

        self.lock_signups_for_concurrency()
        self.invalidate_recordset(["state"])

        state_data = self._get_signup_state_data()
        self._resolve_signup_states(state_data)
        self._fill_signup_state_sources(state_data)

        transition_values, state_updates = self._prepare_signup_state_changes(
            state_data
        )

        transitions = (
            transition_obj.create(transition_values)
            if transition_values
            else transition_obj
        )

        for state, signup_ids in state_updates.items():
            self.browse(signup_ids).write({"state": state})

        if transitions:
            self._on_state_transition(transitions)

        return transitions

    def _on_state_transition(self, transitions):
        """Hook executed after sign-up state transitions are persisted.

        Called once per synchronization, after creating all transition
        records and updating the stored states of the affected sign-ups.

        Receives every transition generated during the synchronization,
        including intermediate transitions, in their creation order.

        The hook runs within the same database transaction. An exception
        raised by an extension rolls back the entire synchronization.

        The hook is not called when no transitions have been created.

        Dependent modules may extend this method using super().

        Args:
            transitions (academy.student.signup.state.transition):
                Recordset containing the newly created transitions.
        """
        pass  # noqa: PIE790

    # =========================================================================
    # Navigation
    # =========================================================================

    # -- Smart buttons --------------------------------------------------------

    def action_view_enrolments(self):
        self.ensure_one()

        additional_context = {
            "default_student_id": self.student_id.id,
            "academy_student_signup_id": self.id,  # para propagación a otros
        }

        return build_act_window_action(
            self.env,
            "academy_base.action_training_action_enrolment_act_window",
            context=additional_context,
            domain=[("id", "in", self.enrolment_ids.ids)],
        )
