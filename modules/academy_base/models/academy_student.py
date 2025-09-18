# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from typing import Required
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import OR
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.addons.phone_validation.tools.phone_validation import phone_format
from odoo.tools import single_email_re

from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import INCLUDE_ARCHIVED_DOMAIN, ARCHIVED_DOMAIN
from ..utils.res_config import get_config_param
from ..utils.helpers import OPERATOR_MAP, one2many_count, is_debug_mode


from logging import getLogger

try:
    # Robust per-country VAT validation if available
    from stdnum import util as stdnum_util
except Exception:
    stdnum_util = None

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
    """A student is a partner who can be enroled on training actions"""

    _name = "academy.student"
    _description = "Academy student"

    _inherit = ["mail.thread"]
    _inherits = {"res.partner": "partner_id"}

    _order = "complete_name ASC, id DESC"
    _rec_names_search = [
        "complete_name",
        "email",
        "ref",
        "vat",
        "company_registry",
    ]

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

    # signup_code = fields.Char(
    #     string="Sign-up code",
    #     required=False,
    #     readonly=True,
    #     index=True,
    #     default=None,
    #     help="Unique sign-up code identifying the student.",
    #     copy=False,
    # )

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

    # -- Field and onchange: creation_mode ------------------------------------

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

    @api.onchange("creation_mode")
    def _onchange_creation_mode(self):
        if self.creation_mode == "from_scratch":
            self.partner_id = None
            self.vat = None
            self.email = None

    # -- Computed field: current_enrolment_ids --------------------------------

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

    # -- Computed field: phone number -----------------------------------------

    call_number = fields.Char(
        string="Call number",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Main number used for calls",
        compute="_compute_phone_number",
        search="_search_phone_number",
    )

    @api.depends("phone", "mobile")
    def _compute_phone_number(self):
        for record in self:
            record.call_number = record.mobile or record.phone

    @api.model
    def _search_phone_number(self, operator, value):
        """Allow searching in call_number as if it were a real field."""
        return [
            "|",
            ("mobile", operator, value),
            ("phone", operator, value),
        ]

    # -- CEFRL Language certificates ------------------------------------------

    cefrl_ids = fields.Many2many(
        string="Languages",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="cefrl.certificate",
        relation="academy_student_cefrl_certificate_rel",
        column1="student_id",
        column2="certificate_id",
        domain=[],
        context={},
    )

    implied_cefrl_ids = fields.Many2many(
        string="Implied languages",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="cefrl.certificate",
        relation="academy_student_implied_cefrl_certificate_rel",
        column1="student_id",
        column2="certificate_id",
        domain=[],
        context={},
        compute="_compute_implied_cefrl_ids",
        search="_search_implied_cefrl_ids",
    )

    @api.depends("cefrl_ids")
    def _compute_implied_cefrl_ids(self):
        for record in self:
            cefrl_set = record.mapped("cefrl_ids")
            cefrl_set += record.mapped("cefrl_ids.implied_ids")

            record.implied_cefrl_ids = cefrl_set

    @api.model
    def _search_implied_cefrl_ids(self, operator, value):
        return [
            "|",
            ("cefrl_ids", operator, value),
            ("cefrl_ids.implied_ids", operator, value),
        ]

    # -- Compute where fields will be required --------------------------------

    email_required = fields.Boolean(
        string="Require email",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="When enabled, an email address is mandatory for this record.",
        compute="_compute_email_required",
        compute_sudo=True,
    )

    @api.depends_context("debug")
    @api.depends("create_date", "write_date", "email")
    def _compute_email_required(self):
        required_value = get_config_param(
            self.env,
            "academy_base.student_email_required",
            cast=str,
            default="except_debug",
            lower=True,
            choices={"never", "always", "except_debug"},
        )

        required = (required_value == "always") or (
            required_value == "except_debug" and not is_debug_mode(self.env)
        )

        for record in self:
            record.email_required = required

    vat_required = fields.Boolean(
        string="Require VAT",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="When enabled, a VAT number is mandatory for this record.",
        compute="_compute_vat_required",
        compute_sudo=True,
    )

    @api.depends_context("debug")
    @api.depends("create_date", "write_date", "vat")
    def _compute_vat_required(self):
        required_value = get_config_param(
            self.env,
            "academy_base.student_vat_required",
            cast=str,
            default="except_debug",
            lower=True,
            choices={"never", "always", "except_debug"},
        )

        required = (required_value == "always") or (
            required_value == "except_debug" and not is_debug_mode(self.env)
        )

        for record in self:
            record.vat_required = required

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [
        (
            "unique_partner",
            "UNIQUE(partner_id)",
            "There is already a student for this contact",
        ),
        # (
        #     "uniq_signup_code_company",
        #     "unique(signup_code, company_id)",
        #     "The sign-up code must be unique per company.",
        # ),
    ]

    @api.constrains("email")
    def _check_email(self):
        required = get_config_param(
            self.env,
            "academy_base.student_email_required",
            cast=str,
            default="except_debug",
            lower=True,
            choices={"never", "always", "except_debug"},
        )

        if (required == "always") or (
            required == "except_debug" and not is_debug_mode(self.env)
        ):
            for record in self:
                email = (getattr(record, "email", "") or "").strip()

                if not email:
                    raise ValidationError(_("Email is required."))

                if not single_email_re.fullmatch(email):
                    raise ValidationError(_("Invalid email: %s") % email)

    @api.constrains("vat")
    def _check_vat(self):
        required = get_config_param(
            self.env,
            "academy_base.student_vat_required",
            cast=str,
            default="except_debug",
            lower=True,
            choices={"never", "always", "except_debug"},
        )

        if (required == "always") or (
            required == "except_debug" and not is_debug_mode(self.env)
        ):
            country_codes = self._get_all_country_codes()
            country_codes = [row.code for row in country_codes if row.code]
            # Foreign companies that trade with non-enterprises in the EU
            # may have a VATIN starting with "EU" instead of a country code.
            country_codes.append("EU")
            print("Check", country_codes)

            for record in self:
                vat = (getattr(record, "vat", "") or "").strip()

                country_code, number = self.partner_id._split_vat(vat)
                has_kwnown_country = (
                    country_code and country_code.upper() in country_codes
                )

                if not (number and has_kwnown_country):
                    error = _("VAT with a known country code is required.")
                    raise ValidationError(error)

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

                domain = OR(leafs)

                if isinstance(record.partner_id.id, int):
                    exclude_self = [("id", "!=", record.partner_id.id)]
                    domain = AND([domain, exclude_self])

                if leafs and partner_obj.search_count(domain) > 1:
                    raise ValidationError(msg)

    @api.constrains("partner_id")
    def _check_unique_student_partner(self):
        for record in self:
            partner = record.partner_id
            if not partner:
                continue

            self.env["res.partner"]._validate_unique_partner_identifiers(
                partner
            )

    # -- Standard methods overrides -------------------------------------------

    @api.model
    def default_get(self, fields):
        values = super(AcademyStudent, self).default_get(fields)

        self._ensure_natural_person(values)

        self._set_default_country(values, fields)

        if "employee" in fields and not values.get("employee", False):
            values["employee"] = False

        if not values.get("firstname") and not values.get("lastname"):
            values["firstname"] = values.get("name", _("New student"))

        return values

    @api.model_create_multi
    def create(self, vals_list):
        self._ensure_signup_date(vals_list)

        category_xid = "academy_base.res_partner_category_student"
        category = self.env.ref(category_xid, raise_if_not_found=False)
        country_codes = self._get_all_country_codes()

        for values in vals_list:
            self._ensure_natural_person(values)
            self._ensure_signup_data(values)
            self._force_student_category(values, category)
            self._vat_prepend_country_code(values, country_codes)

        result = super().create(vals_list)

        result.sanitize_phone_number()

        return result

    def write(self, values):
        """Overridden method 'write'"""

        self._ensure_natural_person(values)
        self._vat_prepend_country_code(values)

        result = super().write(values)

        if "phone" in values or "mobile" in values:
            self.sanitize_phone_number()

        return result

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

    @staticmethod
    def _force_student_category(values, category):
        if category:
            m2m_op = (4, category.id, None)
            if "category_id" not in values:
                values["category_id"] = [m2m_op]
            else:
                values["category_id"].append(m2m_op)

    @api.model
    def _next_signup_code(self, company_id):
        """Return next sign-up code using company-specific sequence,
        falling back to a known default XMLID."""
        sequence_obj = self.env["ir.sequence"].with_company(company_id)

        # 1) Try company-specific sequence (same code, bound to company)
        sequence_domain = [
            ("code", "=", "academy.student.signup.sequence"),
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
        code = sequence_obj.next_by_code("academy.student.signup.sequence")
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
                "code": "academy.student.signup.sequence",
                "xid": "academy_base.ir_sequence_academy_student_signup",
            }
        )

    # -- Auxiliary methods ----------------------------------------------------

    @api.model
    def _get_all_country_codes(self):
        """Fetch all country records with their codes.

        This helper is used in operations on VAT, such as constraints
        or normalization.

        Returns:
            res.country: recordset of countries with the 'code' field loaded
        """
        country_obj = self.env["res.country"]
        return country_obj.search_fetch([], ["code"])

    @api.model
    def _vat_prepend_country_code(self, values, country_data=None):
        """Ensure VAT has the correct country code prefix.

        Args:
            values (dict): dictionary with potential 'vat' and 'country_id'.
            country_data (recordset, optional): cached res.country records.

        Side effects:
            Updates values['vat'] in place if the prefix is missing.
        """

        # Return early if there is no VAT to process
        vat = values.get("vat", False)
        if not vat:
            return

        # Split VAT into country code and number; normalize both
        if len(vat) > 2 and vat[:2].isalpha():
            country_code, number = self.env["res.partner"]._split_vat(vat)
        else:
            country_code, number = None, vat
        country_code = (country_code or "").strip().upper()
        number = (number or "").strip().upper()

        # Load all country codes if they were not preloaded already
        if country_data is None:
            country_data = self._get_all_country_codes()

        # If the already starts with a valid country code, normalize and return
        country_codes = {c.code or "" for c in (country_data or [])}
        if country_code in country_codes:
            values["vat"] = f"{country_code}{number}"
            return

        # Try to get the target country from values or fall back to env
        country_id = values.get("country_id", False)
        if country_id:
            # Works with recordsets and with search_fetch results
            country = next(
                (c for c in (country_data or []) if c.id == country_id), False
            )
        else:
            country = self._get_default_country()
        if not country:
            return

        country_code = (country.code or "").upper()
        if not country_code:
            return

        # Prefix country code and set VAT
        values["vat"] = f"{country_code}{number}"

    @staticmethod
    def _ensure_natural_person(values):
        """Force partner values to always represent a natural person.

        Args:
            values (dict): dictionary of field values to be updated
        """
        values.update(
            type="contact",
            is_company=False,
            company_type="person",
        )

    @api.model
    def _ensure_signup_data(self, values):
        if not values.get("ref"):
            company_id = values.get("company_id") or self.env.company.id
            values["ref"] = self._next_signup_code(company_id)

        if not values.get("signup_date", False):
            values["signup_date"] = fields.Date.context_today(self)

    @api.model
    def _get_default_country(self):
        """Get the default country.

        Priority:
            1. The country set on the current user's partner.
            2. The country set on the current company.
            3. The country set on the company's partner.

        Returns:
            res.country: Country record (may be empty if none found).
        """
        user = self.env.user
        country = user.partner_id.country_id
        if not country:
            country = (
                self.env.company.country_id
                or self.env.company.partner_id.country_id
            )
        return country

    @api.model
    def _set_default_country(self, values, fields):
        """Ensure country_id is set in default_get values.

        Args:
            values (dict): Values dictionary being prepared.
            fields (list): Fields requested by the view.
        """
        if "country_id" in fields and not values.get("country_id", False):
            country = self._get_default_country()

            if country:
                values["country_id"] = country.id

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
