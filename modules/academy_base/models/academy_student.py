# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import OR
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count
from odoo.addons.phone_validation.tools.phone_validation import phone_format

from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import INCLUDE_ARCHIVED_DOMAIN, ARCHIVED_DOMAIN

from logging import getLogger


_logger = getLogger(__name__)


def _make_partner_proxy(method_name):
    """Factory that returns a proxy method delegating to partner_id."""

    def _proxy(self, *args, **kwargs):
        partners = self.mapped("partner_id")
        return getattr(partners, method_name)(*args, **kwargs)

    _proxy.__name__ = method_name
    _proxy.__doc__ = f"Proxy to res.partner.{method_name}"
    return _proxy


class AcademyStudent(models.Model):
    """A student is a partner who can be enrolled on training actions"""

    _name = "academy.student"
    _description = "Academy student"

    _inherit = ["mail.thread"]
    _inherits = {"res.partner": "partner_id"}

    _order = "name ASC"

    partner_id = fields.Many2one(
        string="Partner",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Linked contact record (res.partner) for this student",
        comodel_name="res.partner",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    signup_code = fields.Char(
        string="Sign-up code",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Unique center sign-up code.",
        copy=False,
    )

    signup_date = fields.Date(
        string="Sign-up date",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.context_today(self),
        help="Date the student signed up to the center.",
        tracking=True,
    )

    attainment_id = fields.Many2one(
        string="Educational attainment",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Student’s highest educational attainment",
        comodel_name="academy.educational.attainment",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    birthday = fields.Date(
        string="Date of birth",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Student’s date of birth",
        tracking=True,
    )

    creation_mode = fields.Selection(
        string="Creation Mode",
        required=True,
        readonly=False,
        index=False,
        default="from_scratch",
        help="Create from scratch or use an existing contact.",
        selection=[
            ("from_scratch", "Create from scratch"),
            ("from_existing", "Use existing contact"),
        ],
    )

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

    # -- Computed field: current_enrolment_ids --------------------------------

    current_enrolment_ids = fields.One2many(
        string="Current enrolments",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Enrolments active at the current date/time",
        comodel_name="academy.training.action.enrolment",
        inverse_name="student_id",
        domain=[],
        context={},
        auto_join=False,
        compute="_compute_current_enrolment_ids",
        store=False,
    )

    def _compute_current_enrolment_ids(self):
        now = fields.Datetime.now()
        for record in self:
            record.current_enrolment_ids = record.enrolment_ids.filtered(
                lambda e: (e.register and e.register <= now)
                and (not e.deregister or e.deregister > now)
            )

    # -- Computed field: enrolment_count --------------------------------------

    enrolment_count = fields.Integer(
        string="Nº enrolments",
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

    # -- Computed field: current_enrolment_count ------------------------------

    current_enrolment_count = fields.Integer(
        string="Nº current enrolments",
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
        string="Enrolment str",
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

    # -- Computed field: training_action_ids ----------------------------------

    training_action_ids = fields.Many2many(
        string="Training actions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Training actions with active enrolments",
        comodel_name="academy.training.action",
        relation="academy_training_action_student_rel",
        column1="student_id",
        column2="training_action_id",
        domain=[],
        context={},
        copy=False,
        compute="_compute_training_action_ids",
        search="_search_training_action_ids",
    )

    @api.depends(
        "enrolment_ids",
        "enrolment_ids.training_action_id",
        "enrolment_ids.register",
        "enrolment_ids.deregister",
    )
    def _compute_training_action_ids(self):
        now = fields.Datetime.now()
        for record in self:
            current = record.enrolment_ids.filtered(
                lambda e: (e.register and e.register <= now)
                and (not e.deregister or e.deregister > now)
            )
            record.training_action_ids = current.mapped("training_action_id")

    @api.model
    def _search_training_action_ids(self, operator, value):
        now = fields.Datetime.now()

        return [
            "&",
            ("enrolment_ids.register", "<=", now),
            "|",
            ("enrolment_ids.deregister", "=", False),
            ("enrolment_ids.deregister", ">", now),
            ("enrolment_ids.training_action_id", operator, value),
        ]

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [
        (
            "unique_partner",
            "UNIQUE(partner_id)",
            "There is already a student for this contact",
        ),
        (
            "uniq_signup_code_company",
            "unique(signup_code, company_id)",
            "The sign-up code must be unique per company.",
        ),
    ]

    @api.constrains("partner_id")
    def _check_partner_id(self):
        partner_obj = self.env["res.partner"]
        msg = _("There is already a student with that VAT number or email")

        for record in self:
            if record.partner_id:
                leafs = []

                if record.vat:
                    leafs.append([("vat", "=ilike", record.vat)])

                if record.email:
                    leafs.append([("email", "=ilike", record.email)])

                if leafs and partner_obj.search_count(OR(leafs)) > 1:
                    raise ValidationError(msg)

    # -- Standard methods overrides -------------------------------------------

    @api.model
    def default_get(self, fields):
        parent = super(AcademyStudent, self)
        values = parent.default_get(fields)

        values["employee"] = False
        values["type"] = "contact"
        values["is_company"] = False

        return values

    @api.model_create_multi
    def create(self, vals_list):
        self._ensure_signup_date(vals_list)

        for values in vals_list:
            company_id = values.get("company_id") or self.env.company.id

            if not values.get("signup_code"):
                values["signup_code"] = self._next_signup_code(company_id)

        return super().create(vals_list)

    # -- Public methods -------------------------------------------------------

    def view_enrolments(self):
        self.ensure_one()

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
            "name": _("Enrolments for «{}»").format(self.name),
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

    def view_res_partner(self):
        self.ensure_one()

        action_xid = "base.action_partner_form"
        act_wnd = self.env.ref(action_xid)

        context = (self.env.context or {}).copy()
        context.update(
            {
                "uid": self.env.uid,
                "default_student_id": [(4, 0, self.id)],
                "active_model": "res.partner",
                "active_id": self.partner_id.id,
                "active_ids": [self.partner_id.id],
            }
        )
        domain = self._eval_domain(act_wnd.domain)
        domain = AND([domain, [("student_id", "=", self.id)]])

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "name": act_wnd.name,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
            "target": "new",
            "view_mode": "form",
            "res_id": self.partner_id.id,
            "views": [(False, "form")],
        }

        return serialized

    def sanitize_phone_number(self):
        msg = "Web scoring calculator: Invalid {} number {}. System says: {}"

        country = self.env.company.country_id
        c_code = country.code if country else None
        c_phone_code = country.phone_code if country else None

        for record in self:
            if record.phone:
                try:
                    phone = phone_format(
                        record.phone,
                        c_code,
                        c_phone_code,
                        force_format="INTERNATIONAL",
                    )
                    record.phone = phone
                except Exception as ex:
                    _logger.debug(msg.format("phone", record.phone, ex))

            if record.mobile:
                try:
                    mobile = phone_format(
                        record.mobile,
                        c_code,
                        c_phone_code,
                        force_format="INTERNATIONAL",
                    )
                    record.mobile = mobile
                except Exception as ex:
                    _logger.debug(msg.format("mobile", record.mobile, ex))

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

    # -- Required by res.partner views ----------------------------------------

    def mail_action_blacklist_remove(self):
        return self.partner_id.mail_action_blacklist_remove()

    def create_company(self):
        return self.partner_id.create_company()

    def update_address(self, vals):
        return self.partner_id.update_address(vals)

    def open_commercial_entity(self):
        return self.partner_id.open_commercial_entity()

    def address_get(self, adr_pref=None):
        return self.partner_id.address_get(adr_pref)

    @api.model
    def get_import_templates(self):
        return self.partner_id.get_import_templates()

    # -- Signup sequence methods ----------------------------------------------

    @api.model
    def _ensure_signup_date(self, vals_list):
        today = fields.Date.context_today(self)
        for values in vals_list:
            if not values.get("signup_date"):
                values["signup_date"] = today

    @api.model
    def _next_signup_code(self, company_id):
        """Return next sign-up code using company-specific sequence,
        falling back to a known default XMLID."""
        sequence_obj = self.env["ir.sequence"].with_company(company_id)

        # 1) Try company-specific sequence (same code, bound to company)
        sequence_domain = [
            ("code", "=", "academy.student.signup"),
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
        code = sequence_obj.next_by_code("academy.student.signup")
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
                "code": "academy.student.signup",
                "xid": "academy_base.ir_sequence_academy_student_signup",
            }
        )

    # -- Auxiliary methods ----------------------------------------------------

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
