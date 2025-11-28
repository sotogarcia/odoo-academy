# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import OR
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN

from operator import eq, ne, gt, ge, lt, le
from ..utils.record_utils import ensure_id, ensure_ids
from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import INCLUDE_ARCHIVED_DOMAIN, ARCHIVED_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from logging import getLogger
from datetime import datetime, date, time, timedelta


_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """A student is a partner who can be enrolled on training actions"""

    _name = "academy.student"
    _description = "Academy student"

    _inherit = [
        "academy.support.staff",
    ]

    _order = "complete_name ASC, id DESC"

    _rec_name = "name"
    _rec_names_search = ["name", "email", "signup_code", "vat"]

    enrolment_ids = fields.One2many(
        string="Student enrolments",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="All enrolments: past, current and future",
        comodel_name="academy.training.action.enrolment",
        inverse_name="student_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -- Computed field: enrolment_count --------------------------------------

    enrolment_count = fields.Integer(
        string="No. of enrolments",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Total number of enrolments",
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

    current_enrolment_ids = fields.One2many(
        string="Current enrolments",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Enrolments active at the current date/time",
        comodel_name="academy.training.action.enrolment",
        inverse_name="student_id",
        domain=[
            "&",
            ("register", "<=", fields.Datetime.now()),
            "|",
            ("deregister", "=", False),
            ("deregister", ">", fields.Datetime.now()),
        ],
        context={},
        auto_join=False,
    )

    # -- Computed field: last_deregister --------------------------------------

    last_deregister = fields.Datetime(
        string="End of training",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="End date of the most recent enrolment (empty if still open).",
        compute="_compute_last_deregister",
        search="_search_last_deregister",
    )

    @api.depends(
        "enrolment_ids",
        "enrolment_ids.deregister",
        "enrolment_ids.active",
    )
    @api.depends_context("allowed_company_ids", "force_company")
    def _compute_last_deregister(self):
        self.ensure_one()

        context = self.env.context.copy()
        context.update(active_test=False)

        enrolment_obj = self.env["academy.training.action.enrolment"]
        enrolment_obj = enrolment_obj.with_context(context).sudo()

        now = fields.Datetime.now()
        infinity = datetime.max

        domain = [
            "&",
            "&",
            ("student_id", "in", self.ids),
            ("company_id", "=", self.env.company.id),
            "|",
            ("available_until", "<=", now),
            ("active", "=", True),
        ]
        rows = enrolment_obj.read_group(
            domain=domain,
            fields=["available_until:max"],
            groupby=["student_id"],
            lazy=False,
        )

        last_out = {r["student_id"][0]: r.get("available_until") for r in rows}

        for record in self:
            if record.id not in last_out:
                record.last_deregister = None
            else:
                record.last_deregister = last_out.get(record.id, infinity)

    def _search_last_deregister(self, operator, value):
        """Search students by the deregister date of their most recent
        enrolment within the active company.
        """

        # Ensure the context ignores active_test, to include all enrolments
        context = dict(self.env.context, active_test=False)

        enrolment_obj = (
            self.env["academy.training.action.enrolment"]
            .with_context(context)
            .sudo()
        )

        # Group by student_id and get the latest available_until per company
        rows = enrolment_obj.read_group(
            domain=[("company_id", "=", self.env.company.id)],
            fields=["available_until:max"],
            groupby=["student_id"],
            lazy=False,
        )

        # Build dict: {student_id: last_available_until}
        last_out = {r["student_id"][0]: r.get("available_until") for r in rows}

        # Map Odoo operators to Python comparison functions
        pycmp = {
            "=": eq,
            "==": eq,
            "!=": ne,
            "<>": ne,
            ">": gt,
            "<": lt,
            ">=": ge,
            "<=": le,
        }

        compare = pycmp.get(operator)
        if not compare:
            # Return empty domain for unsupported operators
            return [("id", "in", [])]

        # Normalize search value to datetime if needed
        try:
            value_dt = fields.Datetime.to_datetime(value)
        except Exception:
            value_dt = value

        matched_ids = [
            sid for sid, dt in last_out.items() if dt and compare(dt, value_dt)
        ]

        return [("id", "in", matched_ids)]

    # -- Computed field: current_enrolment_count ------------------------------

    current_enrolment_count = fields.Integer(
        string="No. of current enrolments",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of currently active enrolments",
        compute="_compute_current_enrolment_count",
        search="_search_current_enrolment_count",
    )

    @api.depends(
        "current_enrolment_ids",
        "enrolment_ids.register",
        "enrolment_ids.deregister",
    )
    def _compute_current_enrolment_count(self):
        counts = one2many_count(self, "current_enrolment_ids")

        for record in self:
            record.current_enrolment_count = counts.get(record.id, 0)

    @api.model
    def _search_current_enrolment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "current_enrolment_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Computed field: enrolment_str ----------------------------------------

    enrolment_str = fields.Char(
        string="Enrolment summary",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Current over total enrolments (e.g., “2 / 5”)",
        size=6,
        translate=False,
        compute="_compute_enrolment_str",
    )

    @api.depends(
        "enrolment_ids",
        "current_enrolment_ids",
        "enrolment_count",
        "current_enrolment_count",
    )
    def _compute_enrolment_str(self):
        for record in self:
            current = record.current_enrolment_count or 0
            total = record.enrolment_count or 0

            if total == 0 or current == total:
                record.enrolment_str = str(total)
            else:
                record.enrolment_str = "{} / {}".format(current, total)

    # -- Sign-up proxy
    # -------------------------------------------------------------------------

    signup_ids = fields.One2many(
        string="Per-company sign-up data",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Per-company sign-up records for this student; used to track "
        "onboarding, retention and billing.",
        comodel_name="academy.student.signup",
        inverse_name="student_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    signup_id = fields.Many2one(
        string="Sign-Up",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Sign-up record of this student for the active company, computed "
        "from per-company sign-up data.",
        comodel_name="academy.student.signup",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        compute="_compute_signup_company_values",
    )

    signup_code = fields.Char(
        string="Sign-up code",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Unique code assigned when the student signs up at the centre.",
        size=50,
        translate=False,
        compute="_compute_signup_company_values",
        inverse="_inverse_signup_company_values",
        search="_search_signup_code",
    )

    @api.model
    def _search_signup_code(self, operator, value):
        company_ids = self.env.context.get("allowed_company_ids") or [
            self.env.company.id
        ]
        return [
            "&",
            ("signup_ids.company_id", "in", company_ids),
            ("signup_ids.signup_code", operator, value),
        ]

    signup_date = fields.Datetime(
        string="Sign-up date",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Date and time when the student signed up at the centre.",
        compute="_compute_signup_company_values",
        inverse="_inverse_signup_company_values",
        search="_search_signup_date",
    )

    def _inverse_signup_company_values(self):
        signup_obj = self.env["academy.student.signup"]
        company_id = self.env.company.id

        signup_indexed = self._load_indexed_signups()

        for student in self:
            student_id = student.id
            signup = signup_indexed.get((student_id, company_id))

            values = {}
            if "signup_code" in student._fields:
                values["signup_code"] = student.signup_code or False
            if "signup_date" in student._fields:
                signup_date = student.signup_date or fields.Datetime.now()
                values["signup_date"] = signup_date

            if signup:
                signup.write(
                    {k: v for k, v in values.items() if v is not False}
                )
            else:
                if not values.get("signup_code"):
                    signup_code = signup_obj._next_signup_code(company_id)
                    values["signup_code"] = signup_code
                values.update(student_id=student.id, company_id=company_id)
                signup_obj.create(values)

    @api.model
    def _search_signup_date(self, operator, value):
        company_ids = self.env.context.get("allowed_company_ids") or [
            self.env.company.id
        ]
        return [
            "&",
            ("signup_ids.company_id", "in", company_ids),
            ("signup_ids.signup_date", operator, value),
        ]

    @api.depends(
        "signup_ids.signup_code",
        "signup_ids.signup_date",
        "signup_ids.company_id",
    )
    def _compute_signup_company_values(self):
        signup_indexed = self._load_indexed_signups()
        company_id = self.env.company.id
        for student in self:
            student_id = student.id
            signup = signup_indexed.get((student_id, company_id))
            student.signup_id = signup
            student.signup_code = signup.signup_code if signup else False
            student.signup_date = signup.signup_date if signup else False

    # -- Methods overrides -------------------------------------------

    @api.model
    def _get_relevant_category_external_id(self):
        return "academy_base.res_partner_category_student"

    @api.model_create_multi
    def create(self, values_list):
        """Ensure every new student gets a sign-up row for the active company.
        Inject proxy defaults so their inverse creates `academy.student.signup`
        unless an inline signup_ids for the active company is already provided.
        """
        signup_obj = self.env["academy.student.signup"]
        company_id = self.env.company.id
        now = fields.Datetime.now()

        for values in values_list:
            has_inline = any(
                isinstance(cmd, (list, tuple))
                and len(cmd) >= 3
                and cmd[0] == 0
                and (cmd[2] or {}).get("company_id") == company_id
                for cmd in values.get("signup_ids", [])
            )
            if not has_inline:
                values.setdefault(
                    "signup_code", signup_obj._next_signup_code(company_id)
                )
                values.setdefault("signup_date", now)

        return super().create(values_list)

    # -- Public methods
    # -------------------------------------------------------------------------

    def view_enrolments(self):
        self.ensure_one()

        name = self.env._("Enrolments: {}").format(self.display_name)

        act_xid = "{module}.{name}".format(
            module="academy_base",
            name="action_training_action_enrolment_act_window",
        )
        action = self.env.ref(act_xid)

        view_xid = "{module}.{name}".format(
            module="academy_base",
            name="view_academy_training_action_enrolment_edit_by_user_tree",
        )

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.domain or "[]", {"uid": self.env.uid}))
        ctx.update({"default_student_id": self.id})
        ctx.update({"list_view_ref": view_xid})

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [("student_id", "=", self.id)]])

        action_values = {
            "name": name,
            "type": action.type,
            "help": action.help,
            "domain": domain,
            "context": ctx,
            "res_model": action.res_model,
            "target": action.target,  # "current",
            "view_mode": action.view_mode,
            "search_view_id": action.search_view_id.id,
            "nodestroy": True,
        }

        return action_values

    def fetch_enrolled(
        self, training_actions=None, point_in_time=None, archived=False
    ):
        student_set = self.env["academy.student"]

        domains = []

        if self:
            domain = create_domain_for_ids("student_id", self)
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
            enrolment_obj = self.env["academy.training.action.enrolment"]
            enrolment_set = enrolment_obj.search(AND(domains))
            student_set = enrolment_set.mapped("student_id")

        return student_set

    def perform_signup(self, companies=None):
        """Upsert per-company sign-up for each student in `self` and the
        target company/companies.

        - Creates `academy.student.signup` for each target company if missing,
          generating `signup_code` via the auxiliary model's sequence and using
          current datetime for `signup_date`.
        - If a row already exists, updates it only with non-empty proxy values
          present on the student (`signup_code`, `signup_date`).
        - Returns the `academy.student.signup` recordset for these students
          and the target company/companies.
        """
        self = self.exists()

        signup_obj = self.env["academy.student.signup"]
        company_ids = self._normalize_companies_argument(companies)
        now = fields.Datetime.now()

        if not self or not company_ids:
            return signup_obj.browse()

        # Existing sign-ups for target companies, indexed by (student_id, company_id)
        signup_indexed = self._load_indexed_signups(companies=company_ids)

        to_create = []
        to_update = []

        for student in self:
            for company_id in company_ids:
                existing = signup_indexed.get((student.id, company_id))
                values = self._signup_values(
                    student, company_id, now, existing
                )
                if not existing:
                    to_create.append(values)
                elif values:
                    to_update.append((existing, values))

        if to_create:
            signup_obj.create(to_create)

        for record, values in to_update:
            record.write(values)

        # Return final set for these students and target companies
        domain = [
            ("student_id", "in", self.ids),
            ("company_id", "in", company_ids),
        ]

        return signup_obj.search(domain)

    def revoke_signup(self, companies=None):
        """Delete per-company sign-up rows for each student in `self`.

        If `companies` is not provided, the method removes only the row(s) for
        the active company. Otherwise, it removes rows for the specified
        company/companies.

        Args:
            companies (res.company | int | Iterable[int | res.company] | None):
                Target companies to revoke sign-up data from. When None, only
                the active company is used.

        Returns:
            int: Number of `academy.student.signup` rows deleted.
        """
        self = self.exists()
        if not self:
            return 0

        signup_obj = self.env["academy.student.signup"]
        company_ids = self._normalize_companies_argument(companies)
        if not company_ids:
            return 0

        domain = [
            ("student_id", "in", self.ids),
            ("company_id", "in", company_ids),
        ]
        to_delete = signup_obj.search(domain)
        count = len(to_delete)
        if count:
            to_delete.unlink()
        return count

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def _load_indexed_signups(self, companies=None):
        company_ids = self._normalize_companies_argument(companies)
        student_ids = self.ids

        if not company_ids or not student_ids:
            return {}

        signup_domain = [
            ("company_id", "in", company_ids),
            ("student_id", "in", student_ids),
        ]
        signup_obj = self.env["academy.student.signup"]
        signup_set = signup_obj.search(signup_domain)

        return {
            (s.student_id.id, s.company_id.id): s for s in signup_set if s.id
        }

    @api.model
    def _signup_values(self, student, company, now, existing):
        signup_obj = self.env["academy.student.signup"]

        student_id = ensure_id(student)
        company_id = ensure_id(company)

        signup_code = student.signup_code
        if not signup_code:
            signup_code = signup_obj._next_signup_code(company_id)

        signup_date = student.signup_date or now

        if existing:
            values = {}

            if (
                student.signup_code
                and student.signup_code != existing.signup_code
            ):
                values["signup_code"] = student.signup_code
            if (
                student.signup_date
                and student.signup_date != existing.signup_date
            ):
                values["signup_date"] = student.signup_date
            if not existing.signup_date and "signup_date" not in values:
                values["signup_date"] = now
        else:
            values = {
                "student_id": student_id,
                "company_id": company_id,
                "signup_code": signup_code,
                "signup_date": signup_date,
            }

        return values

    @api.model
    def _normalize_companies_argument(self, companies):
        # Normalize companies -> list of ids
        if companies is None:
            company_ids = [self.env.company.id]
        elif isinstance(companies, (list, tuple, set)):
            company_ids = [ensure_id(c) for c in companies]
        else:
            company_ids = ensure_ids(companies, raise_if_empty=False) or []

        # Clean up and deduplicate
        company_ids = list({cid for cid in company_ids if cid})

        return company_ids
