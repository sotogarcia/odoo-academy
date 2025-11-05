# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from uuid import uuid4
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval
from odoo.tools.misc import str2bool

from validators import url as is_a_valid_url
from logging import getLogger
from lxml import etree


_logger = getLogger(__name__)


class CivilServiceTrackerPublicOffer(models.Model):
    """
    Represents a public employment offer within the civil service system.

    Each public offer is linked to a public administration and an issuing
    authority, and contains one or more selection processes. The model also
    includes metadata such as call year, offer date, reference URLs,
    and a unique token for tracking.
    """

    _name = "civil.service.tracker.public.offer"
    _description = "Civil service tracker public offer"

    _table = "cst_public_offer"

    _rec_name = "name"
    _order = "name ASC"

    _inherit = ["mail.thread", "image.mixin"]

    _rec_names_search = ["name", "short_name"]

    name = fields.Char(
        string="Offer name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name of the public employment offer (e.g. 2024 General OEP)",
        translate=True,
        tracking=True,
        copy=False,
    )

    short_name = fields.Char(
        string="Short name",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Commonly used or internal short name, e.g., "AGE 2019".',
        translate=True,
        tracking=True,
        copy=False,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Additional context or summary of the public offer (optional)",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=True,
        default=True,
        help="Enable or disable this public offer without deleting it",
        tracking=True,
    )

    token = fields.Char(
        string="Token",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: str(uuid4()),
        help="Unique token used to identify and track this public offer",
        translate=False,
        copy=False,
        tracking=True,
    )

    offer_date = fields.Date(
        string="Offer date",
        required=False,
        readonly=False,
        index=True,
        default=fields.Date.today(),
        help="Official date when the offer was approved or published",
        tracking=True,
        copy=False,
    )

    offer_year = fields.Char(
        string="Offer year",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: str(fields.Date.today().year),
        help="Year or years to which the offer applies (YYYY, YYYY,...)",
        translate=False,
        tracking=True,
        copy=False,
    )

    # - Field: public_administration_id (onchange)
    # ------------------------------------------------------------------------

    public_administration_id = fields.Many2one(
        string="Public administration",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Administration responsible for managing this public offer",
        comodel_name="civil.service.tracker.public.administration",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    @api.onchange("public_administration_id")
    def _onchange_public_administration_id(self):
        authority_obj = self.env["civil.service.tracker.issuing.authority"]

        for record in self:
            if not record.public_administration_id:
                continue

            # El registro es nuevo (aún no tiene ID) o no tiene imagen propia
            new_record = not record.id or isinstance(record.id, models.NewId)
            if new_record or not record.image_1920:
                admin_image = record.public_administration_id.image_1920

                # Asignar la imagen de la oferta si existe, si no la de la administración
                record.image_1920 = admin_image

            # Automatic change issuing authority
            if not record.issuing_authority_id:
                partner_id = record.public_administration_id.partner_id.id
                authority_domain = [("partner_id", "=", partner_id)]
                authority_set = authority_obj.search(authority_domain)
                if len(authority_set) == 1:
                    record.issuing_authority_id = authority_set

    # ------------------------------------------------------------------------

    administration_type_id = fields.Many2one(
        string="Administration type",
        readonly=True,
        index=True,
        comodel_name="civil.service.tracker.administration.type",
        help="Specific classification of the administration (e.g. AGE, AEAT).",
        related="public_administration_id.administration_type_id",
        store=True,
        copy=False,
    )

    administration_scope_id = fields.Many2one(
        string="Administration scope",
        readonly=True,
        index=True,
        help="Scope of the administration (e.g. state, regional, local).",
        related=(
            "public_administration_id.administration_type_id."
            "administration_scope_id"
        ),
        store=True,
        copy=False,
    )

    administrative_region_id = fields.Many2one(
        string="Administrative region",
        readonly=True,
        index=True,
        help=False,
        comodel_name="civil.service.tracker.administrative.region",
        related=("public_administration_id.administrative_region_id"),
        store=True,
        tracking=True,
    )

    issuing_authority_id = fields.Many2one(
        string="Issuing authority",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Authority that issued or published this public offer",
        comodel_name="civil.service.tracker.issuing.authority",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    @api.onchange("issuing_authority_id")
    def _onchange_issuing_authority_id(self):
        admin_obj = self.env["civil.service.tracker.public.administration"]

        for record in self:
            # Automatic change public administration
            if not record.public_administration_id:
                partner_id = record.issuing_authority_id.partner_id.id
                domain = [("partner_id", "=", partner_id)]
                administration_set = admin_obj.search(domain)
                if len(administration_set) == 1:
                    record.public_administration_id = administration_set

    delegated_authority_id = fields.Many2one(
        string="Delegated authority",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Delegated or proposing entity (e.g. Secretaría de Estado)",
        comodel_name="res.partner",
        domain=[("is_company", "=", True)],
        context={},
        ondelete="set null",
        auto_join=False,
        tracking=True,
    )

    selection_process_ids = fields.One2many(
        string="Selection processes",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="List of selection processes included in this public offer",
        comodel_name="civil.service.tracker.selection.process",
        inverse_name="public_offer_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    public_process_count = fields.Integer(
        string="Process count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Total number of selection processes in this public offer",
        compute="_compute_public_process_count",
        copy=False,
    )

    @api.depends("selection_process_ids")
    def _compute_public_process_count(self):
        for record in self:
            record.public_process_count = len(record.selection_process_ids)

    bulletin_board_url = fields.Char(
        string="Bulletin board URL",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Link to the bulletin board or notice publication",
        translate=False,
        tracking=True,
    )

    official_journal_url = fields.Char(
        string="Official journal URL",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Link to the official journal or legal source of publication",
        translate=False,
        tracking=True,
        copy=False,
    )

    # - Field: position_total (computed + search)
    # ------------------------------------------------------------------------

    position_total = fields.Integer(
        string="Total positions",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Total number of positions across all vacancy types",
        compute="_compute_position_total",
        search="_search_position_total",
        copy=False,
    )

    @api.depends(
        "selection_process_ids.vacancy_position_ids.position_quantity"
    )
    def _compute_position_total(self):
        map_path = (
            "selection_process_ids.vacancy_position_ids.position_quantity"
        )
        for record in self:
            quantities = record.mapped(map_path)
            record.position_total = sum(quantities)

    @api.model
    def _search_position_total(self, operator, value):
        """
        Custom search for the computed field 'position_total'.

        - For ('=', False) → returns offers with no positions.
        - For ('!=', False) → returns offers with at least one position.
        - Otherwise, filters offers by the sum of all position quantities.
        """
        if operator in ("=", "!=") and not value:
            agg = "COUNT(vp.id)"
            operator = ">" if operator == "=" else "="
            value = 0
        else:
            agg = "COALESCE(SUM(vp.position_quantity), 0)"

        query = f"""
            SELECT
              po.id
            FROM
              cst_public_offer AS po
            LEFT JOIN cst_selection_process AS sp
                ON po.id = sp.public_offer_id
            LEFT JOIN cst_vacancy_position AS vp
                ON sp.id = vp.selection_process_id
            GROUP BY
              po.id
            HAVING
              {agg} {operator} %s
        """

        self._cr.execute(query, (value,))
        matching_ids = [row[0] for row in self._cr.fetchall()]

        return [("id", "in", matching_ids)]

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            "unique_public_offer_name",
            "UNIQUE(name)",
            "The name of the public offer must be unique.",
        ),
        # (
        #     "check_name_min_length",
        #     "CHECK(char_length(name) > 3)",
        #     "The name must have more than 3 characters.",
        # ),
        (
            "unique_public_offer_short_name",
            "UNIQUE(short_name)",
            "The short name of the public offer must be unique.",
        ),
        # (
        #     "check_short_name_min_length",
        #     "CHECK(char_length(name) > 3)",
        #     "The short name must have more than 3 characters.",
        # ),
        (
            "unique_public_offer_token",
            "UNIQUE(token)",
            "The token must be unique.",
        ),
        (
            "issuing_and_delegated_must_differ",
            """CHECK(
                issuing_authority_id IS DISTINCT FROM delegated_authority_id
            )""",
            "The delegated authority must differ from the issuing authority.",
        ),
        (
            "valid_year_list",
            "CHECK (offer_year IS NULL OR offer_year ~ '^\\s*\\d{4}\\s*(,\\s*\\d{4}\\s*)*$')",
            "Only four-digit years, separated by commas, are allowed.",
        ),
    ]

    @api.constrains("bulletin_board_url")
    def _check_bulletin_board_url(self):
        message_pattern = _("Invalid bulletin board URL: %s")

        for record in self:
            url = record.bulletin_board_url
            if url and not is_a_valid_url(url):
                raise ValidationError(message_pattern % url)

    @api.constrains("official_journal_url")
    def _check_official_journal_url(self):
        message_pattern = _("Invalid official journal URL: %s")

        for record in self:
            url = record.official_journal_url
            if url and not is_a_valid_url(url):
                raise ValidationError(message_pattern % url)

    # -------------------------------------------------------------------------
    # OVERWRITTEN METHODS
    # -------------------------------------------------------------------------

    @api.depends("short_name", "name")
    @api.depends_context("lang")
    def _compute_display_name(self):
        config = self.env["ir.config_parameter"].sudo()
        param_name = "civil_service_tracker.display_process_short_name"

        raw_value = config.get_param(param_name, default="False")
        use_short = str2bool(raw_value)

        for record in self:
            if use_short and record.short_name:
                record.display_name = record.short_name
            else:
                record.display_name = record.name

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        parent = super(CivilServiceTrackerPublicOffer, self)

        result = parent.fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )

        if view_type == "search":
            arch = etree.fromstring(result["arch"])
            current_year = fields.Date.today().year

            placeholder = arch.xpath("//group[@string='__YEAR_FILTERS__']")

            if placeholder:
                grp = placeholder[0]

                for label, yr in [
                    (_("Previous year"), current_year - 1),
                    (_("Current year"), current_year),
                    (_("Next year"), current_year + 1),
                ]:
                    flt = etree.Element(
                        "filter",
                        {
                            "string": label,
                            "name": f"filter_offer_year_{yr}",
                            "domain": f"[('offer_year','=',{yr})]",
                        },
                    )
                    grp.append(flt)

                grp.set("string", "")

            result["arch"] = etree.tostring(arch, encoding="unicode")

        return result

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        for values in values_list:
            self._normalize_years_string(values)
            self._ensure_offer_name(values)

        parent = super(CivilServiceTrackerPublicOffer, self)
        result = parent.create(values_list)

        return result

    def write(self, values):
        """Overridden method 'write'"""

        self._normalize_years_string(values)

        parent = super(CivilServiceTrackerPublicOffer, self)
        result = parent.write(values)

        return result

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """Prevents new record of the inherited (_inherits) model will be
        created
        """

        uuid = str(uuid4())[-12:]
        context = self.env.context

        new_name = context.get("default_name", False)
        if not new_name:
            new_name = f"{self.name} - {uuid}"

        default = dict(default or {})
        default.update({"name": new_name})

        parent = super(CivilServiceTrackerPublicOffer, self)
        result = parent.copy(default)

        for process in self.selection_process_ids:
            ctx = context.copy()
            ctx.update({"default_name": f"{process.name} - {uuid}"})
            process.with_context(ctx).copy({"public_offer_id": result.id})

        return result

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value

        if value is None:
            return False

        return str(value).strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def _normalize_years_string(values):
        """Clean and normalize a comma-separated list of years."""
        raw_value = values.get("offer_year")
        if not raw_value:
            return

        year_list = raw_value.split(",")
        years = [year.strip() for year in year_list if year.strip()]

        if years:
            values["offer_year"] = ",".join(years).strip()

    def _ensure_offer_name(self, values):
        values = values or {}

        name = values.get("name", None)
        if name:
            return

        admon_id = values.get("public_administration_id", None)
        admon_obj = self.env["civil.service.tracker.public.administration"]
        admon = admon_obj.browse(admon_id)
        if not admon:
            return

        offer_year = values.get("offer_year", None)
        if not offer_year:
            return

        values["name"] = f"{admon.name}, {offer_year}"

        if admon.short_name:
            values["short_name"] = f"{admon.short_name}, {offer_year}"

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def view_selection_process(self):
        self.ensure_one()

        action_xid = (
            "civil_service_tracker."
            "action_civil_services_selection_process_act_window"
        )
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_public_offer_id": self.id})

        domain = [("public_offer_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": act_wnd.name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized
