###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.osv.expression import AND, FALSE_DOMAIN
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

from ..utils.helpers import (
    OPERATOR_MAP,
    one2many_count,
    one2many_count_search_domain,
)
from ..utils.record_utils import (
    ARCHIVED_DOMAIN,
    INCLUDE_ARCHIVED_DOMAIN,
    create_domain_for_ids,
    create_domain_for_interval,
    ensure_id,
    ensure_ids,
)


class AcademyStudent(models.Model):
    """A student is a partner who can be enrolled on training actions"""

    _name = "academy.student"
    _description = "Academy student"

    _inherit = [  # noqa: RUF012
        "academy.support.staff",
    ]

    _order = "complete_name ASC, id DESC"

    _rec_name = "name"
    _rec_names_search = ["name", "email", "signup_code", "vat"]  # noqa: RUF012

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
        return one2many_count_search_domain(
            self,
            "enrolment_ids",
            operator,
            value,
        )

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
            ("is_current", "=", True),
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
        help=(
            "Latest effective enrolment end used for retention calculations "
            "in the active company. Open-ended enrolments are treated as "
            "having an indefinite end."
        ),
        compute="_compute_last_deregister",
        search="_search_last_deregister",
    )

    @api.depends(
        "enrolment_ids",
        "enrolment_ids.available_until",
        "enrolment_ids.active",
    )
    @api.depends_context("allowed_company_ids", "force_company")
    def _compute_last_deregister(self):
        context = self.env.context.copy()
        context.update(active_test=False)

        enrolment_obj = self.env["academy.training.action.enrolment"]
        enrolment_obj = enrolment_obj.with_context(context).sudo()

        domain = self._get_last_deregister_domain(self.ids)

        rows = enrolment_obj.read_group(
            domain=domain,
            fields=["available_until:max"],
            groupby=["student_id"],
            lazy=False,
        )

        last_out = {
            row["student_id"][0]: row.get("available_until")
            for row in rows
            if row.get("student_id")
        }

        for record in self:
            record.last_deregister = last_out.get(record.id, False)

    def _search_last_deregister(self, operator, value):
        """Search students by their latest effective enrolment end."""

        context = dict(self.env.context, active_test=False)

        enrolment_obj = (
            self.env["academy.training.action.enrolment"]
            .with_context(context)
            .sudo()
        )

        last_deregister_domain = self._get_last_deregister_domain()

        rows = enrolment_obj.read_group(
            domain=last_deregister_domain,
            fields=["available_until:max"],
            groupby=["student_id"],
            lazy=False,
        )

        last_out = {
            row["student_id"][0]: row.get("available_until")
            for row in rows
            if row.get("student_id")
        }

        operator = {
            "==": "=",
            "<>": "!=",
        }.get(operator, operator)

        if value in (False, None):
            student_ids = list(last_out)

            if operator == "=":
                return [("id", "not in", student_ids)]

            if operator == "!=":
                return [("id", "in", student_ids)]

            return FALSE_DOMAIN

        compare = OPERATOR_MAP.get(operator)
        if not compare:
            return FALSE_DOMAIN

        try:
            value_dt = fields.Datetime.to_datetime(value)
        except (TypeError, ValueError):
            return FALSE_DOMAIN

        matched_ids = [
            student_id
            for student_id, last_deregister in last_out.items()
            if last_deregister and compare(last_deregister, value_dt)
        ]

        return [("id", "in", matched_ids)] if matched_ids else FALSE_DOMAIN

    @api.model
    def _get_last_deregister_domain(self, student_ids=None):
        now = fields.Datetime.now()

        domain = [
            "&",
            ("company_id", "=", self.env.company.id),
            "|",
            ("available_until", "<=", now),
            ("active", "=", True),
        ]

        if student_ids is not None:
            domain = AND(
                [
                    domain,
                    [("student_id", "in", student_ids)],
                ]
            )

        return domain

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
        return one2many_count_search_domain(
            self,
            "current_enrolment_ids",
            operator,
            value,
        )

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
                record.enrolment_str = f"{current} / {total}"

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
        return [
            "&",
            ("signup_ids.company_id", "=", self.env.company.id),
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

                values.update(
                    student_id=student.id,
                    company_id=company_id,
                )
                signup_obj.create(values)

    @api.model
    def _search_signup_date(self, operator, value):
        return [
            "&",
            ("signup_ids.company_id", "=", self.env.company.id),
            ("signup_ids.signup_date", operator, value),
        ]

    @api.depends(
        "signup_ids.signup_code",
        "signup_ids.signup_date",
        "signup_ids.company_id",
    )
    @api.depends_context("company")
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

        self._update_signup_data_if_auto(values_list)
        result = super().create(values_list)

        return result

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
        ctx.update(safe_eval(action.context or "{}", {"uid": self.env.uid}))
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
        - If a row already exists, updates it only with non-empty proxy
          values for the corresponding target company (`signup_code`,
          `signup_date`).
        - Returns the `academy.student.signup` recordset for these students
          and the target company/companies.
        """
        student_set = self.exists()

        company_ids = student_set._normalize_companies_argument(companies)
        if not student_set or not company_ids:
            return self.env["academy.student.signup"].browse()

        student_set._ensure_signup_company_access(company_ids)

        allowed_company_ids = list(
            student_set.env.context.get("allowed_company_ids")
            or [student_set.env.company.id]
        )

        for company_id in company_ids:
            if company_id not in allowed_company_ids:
                allowed_company_ids.append(company_id)

        student_set = student_set.with_context(
            allowed_company_ids=allowed_company_ids
        )

        signup_obj = student_set.env["academy.student.signup"]
        now = fields.Datetime.now()

        signup_indexed = student_set._load_indexed_signups(
            companies=company_ids
        )

        company_indexed = {
            company.id: company
            for company in student_set.env["res.company"].browse(company_ids)
        }

        to_create = []
        to_update = []

        for student in student_set:
            for company_id in company_ids:
                company = company_indexed[company_id]
                existing = signup_indexed.get((student.id, company_id))

                values = student_set._signup_values(
                    student,
                    company,
                    now,
                    existing,
                )

                if not existing:
                    to_create.append(values)
                elif values:
                    to_update.append((existing, values))

        if to_create:
            signup_obj.create(to_create)

        for record, values in to_update:
            record.write(values)

        domain = [
            ("student_id", "in", student_set.ids),
            ("company_id", "in", company_ids),
        ]

        return signup_obj.search(domain)

    def revoke_signup(self, companies=None):
        student_set = self.exists()

        company_ids = student_set._normalize_companies_argument(companies)
        if not student_set or not company_ids:
            return 0

        student_set._ensure_signup_company_access(company_ids)

        allowed_company_ids = list(
            student_set.env.context.get("allowed_company_ids")
            or [student_set.env.company.id]
        )

        for company_id in company_ids:
            if company_id not in allowed_company_ids:
                allowed_company_ids.append(company_id)

        student_set = student_set.with_context(
            allowed_company_ids=allowed_company_ids
        )

        signup_obj = student_set.env["academy.student.signup"]

        domain = [
            ("student_id", "in", student_set.ids),
            ("company_id", "in", company_ids),
        ]

        to_delete = signup_obj.search(domain)
        count = len(to_delete)

        if count:
            to_delete.unlink()

        return count

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def _update_signup_data_if_auto(self, values_list):
        """Injects required sign-up data (code and date) into the creation
        values for students that must be auto-signed up.

        This method verifies if the active company has auto-signup enabled.

        :param values_list: A list of dictionaries containing the creation
                            values for 'academy.student'.
        :return: True if the operation was performed (auto-signup enabled
                 and data prepared), False otherwise (auto-signup disabled).
        :rtype: bool
        """
        company = self.env.company
        if not company or not company.auto_signup:
            return False

        signup_obj = self.env["academy.student.signup"]
        company_id = company.id
        now = fields.Datetime.now()

        if isinstance(values_list, dict):
            target_list = [values_list]
        else:
            target_list = values_list

        for values in target_list:
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

        return True

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

        company_student = student.with_company(company)

        signup_code = company_student.signup_code
        if not signup_code:
            signup_code = signup_obj._next_signup_code(company_id)

        signup_date = company_student.signup_date or now

        if existing:
            values = {}

            if (
                company_student.signup_code
                and company_student.signup_code != existing.signup_code
            ):
                values["signup_code"] = company_student.signup_code

            if (
                company_student.signup_date
                and company_student.signup_date != existing.signup_date
            ):
                values["signup_date"] = company_student.signup_date

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
            company_ids = [ensure_id(rc_id) for rc_id in companies]
        else:
            company_ids = ensure_ids(companies, raise_if_empty=False) or []

        # Clean up and deduplicate
        company_ids = list(dict.fromkeys(cid for cid in company_ids if cid))

        return company_ids

    def _ensure_signup_company_access(self, company_ids):
        """Ensure the user can manage sign-ups for the target companies.

        Args:
            company_ids (iterable[int]): Company IDs for which sign-up data will
                be managed.

        Returns:
            None

        Raises:
            AccessError: If the user is not allowed to manage one or more target
                companies.
        """
        user_company_ids = set(self.env.user.company_ids.ids)
        target_company_ids = set(company_ids)

        if not target_company_ids.issubset(user_company_ids):
            raise AccessError(
                _("You are not allowed to manage sign-ups for some companies.")
            )
