# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools import single_email_re
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.phone_validation.tools.phone_validation import phone_format
from odoo.osv.expression import AND

from ..utils.res_config import get_config_param
from ..utils.helpers import is_debug_mode

from logging import getLogger

_logger = getLogger(__name__)


class AcademyMemberMixin(models.AbstractModel):
    _name = "academy.member.mixin"
    _description = (
        "Common fields and methods for all models that represent "
        "people within the academy community."
    )

    _inherits = {"res.partner": "partner_id"}

    partner_id = fields.Many2one(
        string="Partner",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Linked contact record (res.partner) for this record",
        comodel_name="res.partner",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    signup_date = fields.Date(
        string="Sign-up date",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.context_today(self),
        help="Date the contact signed up at the center.",
        tracking=True,
    )

    birthday = fields.Date(
        string="Date of birth",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Contact date of birth",
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

    cefrl_ids = fields.Many2many(
        string="Languages",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="cefrl.certificate",
        # relation="academy_student_cefrl_certificate_rel",
        column1="person_id",
        column2="certificate_id",
        domain=[],
        context={},
    )

    # -- Computed field: implied_cefrl_ids ------------------------------------

    implied_cefrl_ids = fields.Many2many(
        string="Implied languages",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="cefrl.certificate",
        # relation="academy_student_implied_cefrl_certificate_rel",
        column1="person_id",
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
            "academy_base.partner_email_required",
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
            "academy_base.partner_vat_required",
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
            "There is already a record for this contact",
        ),
    ]

    @api.constrains("email")
    def _check_email(self):
        required = get_config_param(
            self.env,
            "academy_base.partner_email_required",
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
            "academy_base.partner_vat_required",
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

            for record in self:
                vat = (getattr(record, "vat", "") or "").strip()

                country_code, number = self.partner_id._split_vat(vat)
                has_known_country = (
                    country_code and country_code.upper() in country_codes
                )

                if not (number and has_known_country):
                    error = _("VAT with a known country code is required.")
                    raise ValidationError(error)

    # -- Public exported methods ----------------------------------------

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

    def view_res_partner(self):
        self.ensure_one()

        action_xid = "base.action_partner_form"
        act_wnd = self.env.ref(action_xid)

        inverse_field = self._get_inverse_field_name()
        context_default_inverse_field = f"default_{inverse_field}"

        context = (self.env.context or {}).copy()
        context.update(
            {
                "uid": self.env.uid,
                context_default_inverse_field: [(4, self.id, 0)],
                "active_model": "res.partner",
                "active_id": self.partner_id.id,
                "active_ids": [self.partner_id.id],
            }
        )
        domain = self._eval_domain(act_wnd.domain)
        domain = AND([domain, [(inverse_field, "=", self.id)]])

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

    # -- Required by res.partner views ----------------------------------------

    def update_address(self, vals):
        partner_set = self._get_partner_with_context()
        return partner_set.update_address(vals)

    def open_commercial_entity(self):
        partner_set = self._get_partner_with_context()
        return partner_set.open_commercial_entity()

    def address_get(self, adr_pref=None):
        partner_set = self._get_partner_with_context()
        return partner_set.address_get(adr_pref=None)

    @api.model
    def view_header_get(self, view_id, view_type):
        partner_set = self._get_partner_with_context()
        return partner_set.view_header_get(view_id, view_type)

    @api.model
    def get_import_templates(self):
        partner_set = self._get_partner_with_context()
        return partner_set.get_import_templates()

    def mail_action_blacklist_remove(self):
        partner_set = self._get_partner_with_context()
        return partner_set.partner_id.mail_action_blacklist_remove()

    def create_company(self):
        partner_set = self._get_partner_with_context()
        return partner_set.partner_id.create_company()

    @api.model
    @api.returns("self", lambda value: value.id)
    def find_or_create(self, email, assert_valid_email=False):
        self.partner_id.find_or_create(email, assert_valid_email=False)

    @api.readonly
    @api.model
    def im_search(self, name, limit=20, excluded_ids=None):
        self.partner_id.im_search(name, limit=20, excluded_ids=None)

    @api.readonly
    @api.model
    def get_mention_suggestions(self, search, limit=8):
        self.partner_id.get_mention_suggestions(search, limit=8)

    # -- Base model methods overrides -----------------------------------------

    @api.model
    def default_get(self, fields):
        values = super().default_get(fields)

        self._ensure_natural_person(values)

        self._set_default_country(values, fields)

        if "employee" in fields and not values.get("employee", False):
            values["employee"] = False

        if not values.get("firstname") and not values.get("lastname"):
            values["firstname"] = values.get("name", _("Creating new"))

        return values

    @api.model_create_multi
    def create(self, vals_list):
        category_xid = self._get_relevant_category_external_id()
        category = self.env.ref(category_xid, raise_if_not_found=False)
        country_codes = self._get_all_country_codes()

        for values in vals_list:
            self._ensure_natural_person(values)
            self._vat_prepend_country_code(values, country_codes)
            self._force_category(values, category)
            self._ensure_signup_data(values)

        result = super().create(vals_list)

        if any(("phone" in v) or ("mobile" in v) for v in vals_list):
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

    # -- Auxiliary methods ----------------------------------------------------

    @staticmethod
    def _force_category(values, category, raise_if_not_category=False):
        if category and len(category) == 1:
            m2m_op = (4, category.id, 0)
            if "category_id" not in values:
                values["category_id"] = [m2m_op]
            else:
                values["category_id"].append(m2m_op)

        elif raise_if_not_category:
            message = _("Parameter 'category' must be a single category.")
            raise ValidationError(message)

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
        signup_code = self._get_relevant_signup_sequence_code()
        sequence_domain = [
            ("code", "=", signup_code),
            ("company_id", "=", company_id),
        ]
        sequence = sequence_obj.search(sequence_domain, limit=1)
        if sequence:
            return sequence.with_company(company_id).next_by_id()

        # 2) Explicit fallback to the known default sequence XMLID
        sequence_xid = self._get_relevant_signup_sequence_external_id()
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
                "Missing sequence for partner sign-up. "
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
        if not values.get("ref"):
            company_id = values.get("company_id") or self.env.company.id
            values["ref"] = self._next_signup_code(company_id)
            values["barcode"] = values["ref"]

        if not values.get("signup_date", False):
            values["signup_date"] = fields.Date.context_today(self)

    def _get_partner_with_context(self):
        partner_set = self.mapped("partner_id")

        context = self.env.context.copy()
        context.update(active_model="res.partner")

        if len(self.partner_id) == 1:
            context.update(active_id=self.partner_id.id)
        elif len(self.partner_id) > 1:
            context.update(active_ids=self.partner_id.ids)

        return partner_set.with_context(context)

    # -- Methods need to be implemented in derivated models -------------------

    @api.model
    def _get_relevant_category_external_id(self):
        """e.g.: academy_base.res_partner_category_student"""
        name = "_get_relevant_category_external_id"
        message = _(f"Method '{name}' must be implemented before being used.")
        raise NotImplementedError(message)

    @api.model
    def _get_relevant_signup_sequence_code(self):
        """e.g: academy.student.signup.sequence"""
        name = "_get_relevant_signup_sequence_code"
        message = _(f"Method '{name}' must be implemented before being used.")
        raise NotImplementedError(message)

    @api.model
    def _get_relevant_signup_sequence_external_id(self):
        """e.g.: academy_base.ir_sequence_academy_student_signup"""
        name = "_get_relevant_signup_sequence_external_id"
        message = _(f"Method '{name}' must be implemented before being used.")
        raise NotImplementedError(message)

    @api.model
    def _get_inverse_field_name(self):
        """e.g.: student_id"""
        name = "_get_inverse_field_name"
        message = _(f"Method '{name}' must be implemented before being used.")
        raise NotImplementedError(message)
