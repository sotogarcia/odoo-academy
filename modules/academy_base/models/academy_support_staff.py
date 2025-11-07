# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools import single_email_re
from odoo.tools.misc import file_path
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.phone_validation.tools.phone_validation import phone_format
from odoo.osv.expression import AND

from ..utils.res_config import get_config_param
from ..utils.helpers import is_debug_mode

from base64 import b64encode
from pytz import timezone, utc
from datetime import datetime, time
from collections.abc import Iterable

from logging import getLogger

_logger = getLogger(__name__)


class AcademySupportStaff(models.Model):
    _name = "academy.support.staff"
    _description = "Academy support staff member"

    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]

    _inherits = {"res.partner": "partner_id"}

    _order = "complete_name ASC, id DESC"

    _rec_name = "complete_name"
    _rec_names_search = [
        "complete_name",
        "email",
        "vat",
        "company_registry",
    ]

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

    # -- Business fields ------------------------------------------------------

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

    has_custom_avatar = fields.Boolean(
        string="Has custom avatar",
        required=False,
        readonly=True,
        index=False,
        default=False,
        help="True if this partner uses a custom avatar False otherwise.",
        store=False,
        compute="_compute_has_custom_avatar",
    )

    _default_avatar_b64 = None  # class-level cache

    def _get_default_avatar_b64(self):
        """Return the default avatar, cached at class level."""
        if not type(self)._default_avatar_b64:
            new_partner = self.env["res.partner"].new()
            type(self)._default_avatar_b64 = new_partner.avatar_128

        return type(self)._default_avatar_b64

    def _compute_has_custom_avatar(self):
        default_b64 = self._get_default_avatar_b64()
        for rec in self:
            avatar = rec.avatar_128 or b""
            rec.has_custom_avatar = bool(avatar and avatar != default_b64)

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

                country_code, number = self._split_vat(vat)
                has_known_country = (
                    country_code and country_code.upper() in country_codes
                )

                if not (number and has_known_country):
                    error = _("VAT with a known country code is required.")
                    raise ValidationError(error)

    # -- Public exported methods ----------------------------------------

    def sanitize_phone_number(self):
        self._sanitize_phone_number(self)

        return self

    def view_res_partner(self):
        self.ensure_one()

        action_xid = "base.action_partner_form"
        act_wnd = self.env.ref(action_xid)

        context = (self.env.context or {}).copy()
        domain = self._eval_domain(act_wnd.domain)
        domain = AND([domain, [("id", "=", self.partner_id.id)]])

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

        self._sanitize_phone_number(vals_list)

        for values in vals_list:
            self._ensure_natural_person(values)
            self._vat_prepend_country_code(values, country_codes)
            self._force_category(values, category)

        result = super().create(vals_list)

        return result

    def write(self, values):
        """Overridden method 'write'"""

        self._sanitize_phone_number(values)

        self._ensure_natural_person(values)
        self._vat_prepend_country_code(values)

        result = super().write(values)

        return result

    def unlink(self):
        """Overridden method 'unlink'"""

        category_xid = self._get_relevant_category_external_id()
        category = self.env.ref(category_xid, raise_if_not_found=False)
        if category:
            category_id = category.id
            partner_set = self.mapped("partner_id")
            partner_set.write({"category_id": [(3, category_id)]})

        return super().unlink()

    # -- Auxiliary methods ----------------------------------------------------

    def _split_vat(self, vat):
        """
        Splits the VAT Number to get the country code in a first place and the
        code itself in a second place.
        This has to be done because some countries' code are one character
        long instead of two (i.e. "T" for Japan)
        """
        if len(vat) > 1 and vat[1].isalpha():
            vat_country, vat_number = vat[:2].lower(), vat[2:].replace(" ", "")
        else:
            vat_country, vat_number = vat[:1].lower(), vat[1:].replace(" ", "")

        return vat_country, vat_number

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
            country_code, number = self._split_vat(vat)
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

    @api.model
    def _sanitize_phone_number(self, targets):
        msg = "Web scoring calculator: Invalid {} number {}. System says: {}"

        def _custom_set(item, key, value):
            item[key] = value

        if not targets:
            return

        if not isinstance(targets, Iterable) or isinstance(targets, dict):
            targets = [targets]

        if isinstance(targets, (list, tuple)) and isinstance(targets[0], dict):
            _get, _set = dict.get, _custom_set

        elif isinstance(targets, models.Model):
            _get, _set = getattr, setattr
        else:
            message = _("targets arguemnt must be a dict or recordset not %s")
            raise ValidationError(message % type(targets))

        company = (
            self.env.company
            or self.env.user.company_id
            or self.env.ref("base.main_company", raise_if_not_found=False)
        )

        c_code, c_phone_code = None, None
        if company and company.country_id:
            country = company.country_id
            if country:
                c_code, c_phone_code = country.code, country.phone_code

        phone_fields = ["phone", "mobile"]
        for target in targets:
            for phone_field in phone_fields:
                phone_value = _get(target, phone_field, False)
                if not phone_value:
                    continue

                try:
                    phone_value = phone_format(
                        phone_value,
                        c_code,
                        c_phone_code,
                        force_format="INTERNATIONAL",
                    )
                    _set(target, phone_field, phone_value)
                except Exception as ex:
                    _logger.debug(msg.format(phone_field, phone_value, ex))

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
        return "academy_base.res_partner_category_support_staff"
