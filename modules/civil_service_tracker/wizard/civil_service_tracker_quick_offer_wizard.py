# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerOfferQuickOfferWizard(models.TransientModel):
    _name = "civil.service.tracker.quick.offer.wizard"
    _description = "Civil service tracker offer batch creation wizard"

    _table = "cst_quick_offer_wizard"

    _rec_name = "id"
    _order = "id DESC"

    state = fields.Selection(
        string="Wizard step",
        required=True,
        readonly=False,
        index=False,
        default="step1",
        help=(
            "Internal step of the wizard. Controls which inputs are shown "
            "at each stage."
        ),
        selection=[
            ("step1", "Step 1"),
            ("step2", "Step 2"),
            ("step3", "Step 3"),
        ],
    )

    @api.onchange("state")
    def _onchange_state(self):
        if self.state == "step3":
            self.wizard_line_ids = self._build_wizard_line_commands()

    public_administration_id = fields.Many2one(
        string="Public administration",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=(
            "Public administration responsible for this offer "
            "(e.g. AGE, Xunta, etc.)"
        ),
        comodel_name="civil.service.tracker.public.administration",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.onchange("public_administration_id")
    def _onchange_public_administration_id(self):
        position_domain = self._compute_service_position_domain()

        # Automatic change issuing authority
        authority_obj = self.env["civil.service.tracker.issuing.authority"]
        if self.public_administration_id and not self.issuing_authority_id:
            partner_id = self.public_administration_id.partner_id.id
            authority_domain = [("partner_id", "=", partner_id)]
            authority_set = authority_obj.search(authority_domain)
            if len(authority_set) == 1:
                self.issuing_authority_id = authority_set

        # Automatic select service position
        position_obj = self.env["civil.service.tracker.service.position"]
        self.service_position_ids = position_obj.search(position_domain)

    offer_year = fields.Char(
        string="Offer year(s)",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: str(fields.Date.today().year),
        help=(
            "Year or years to which the offer applies, in the format YYYY "
            "or YYYY,YYYY,... (e.g. 2024 or 2024,2025)"
        ),
        translate=False,
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
    )

    @api.onchange("issuing_authority_id")
    def _onchange_issuing_authority_id(self):
        admin_obj = self.env["civil.service.tracker.public.administration"]

        # Automatic change public administration
        if self.issuing_authority_id and not self.public_administration_id:
            partner_id = self.issuing_authority_id.partner_id.id
            domain = [("partner_id", "=", partner_id)]
            administration_set = admin_obj.search(domain)
            if len(administration_set) == 1:
                self.public_administration_id = administration_set

    offer_date = fields.Date(
        string="Offer date",
        required=False,
        readonly=False,
        index=True,
        default=lambda self: fields.Date.context_today(self),
        help="Date when the public offer was officially approved or published.",
    )

    public_offer_id = fields.Many2one(
        string="Public offer",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=(
            "Public offer used as a reference for this batch of selection "
            "processes."
        ),
        comodel_name="civil.service.tracker.public.offer",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.onchange("public_offer_id")
    def _onchange_public_offer_id(self):
        for record in self:
            offer = record.public_offer_id
            if not offer:
                continue

            record.offer_date = offer.offer_date
            record.issuing_authority_id = offer.issuing_authority_id
            record.bulletin_board_url = offer.bulletin_board_url
            record.official_journal_url = offer.official_journal_url

    public_offer_count = fields.Integer(
        string="Available offers",
        # required=True,
        readonly=True,
        index=False,
        default=0,
        help="Total number of available public offers",
        compute="_compute_public_offer_count",
    )

    @api.depends("public_administration_id", "offer_year")
    def _compute_public_offer_count(self):
        PublicOffer = self.env["civil.service.tracker.public.offer"]

        for record in self:
            domain = record._compute_public_offer_domain()
            record.public_offer_count = PublicOffer.search_count(domain)

    bulletin_board_url = fields.Char(
        string="Bulletin board URL",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Link to the bulletin board or notice publication",
        translate=False,
    )

    official_journal_url = fields.Char(
        string="Official journal URL",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Link to the official journal or legal source of publication",
        translate=False,
    )

    contract_type_ids = fields.Many2many(
        string="Contract type",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_contract_type_ids(),
        help="Contract types applicable to this offer (e.g. career, interim)",
        comodel_name="civil.service.tracker.contract.type",
        relation="cst_quick_offer_wizard_contract_type_rel",
        column1="wizard_id",
        column2="contract_type_id",
        domain=[],
        context={},
    )

    def default_contract_type_ids(self):
        external_name = "civil_service_tracker_contract_type_career"
        external_id = f"civil_service_tracker.{external_name}"
        return self.env.ref(external_id, raise_if_not_found=False)

    access_type_ids = fields.Many2many(
        string="Access type",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_access_type_ids(),
        help=(
            "Access types to be included (e.g. free access, internal "
            "promotion)"
        ),
        comodel_name="civil.service.tracker.access.type",
        relation="cst_quick_offer_wizard_access_type_rel",
        column1="wizard_id",
        column2="access_type_id",
        domain=[],
        context={},
    )

    def default_access_type_ids(self):
        external_name = "civil_service_tracker_access_type_free_access"
        external_id = f"civil_service_tracker.{external_name}"
        return self.env.ref(external_id, raise_if_not_found=False)

    selection_method_ids = fields.Many2many(
        string="Selection method",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_selection_method_ids(),
        help="Selection methods applicable (e.g. exam, merit-based)",
        comodel_name="civil.service.tracker.selection.method",
        relation="cst_quick_offer_wizard_selection_method_rel",
        column1="wizard_id",
        column2="selection_method_id",
        domain=[],
        context={},
    )

    def default_selection_method_ids(self):
        external_name = "selection_method_exam"
        external_id = f"civil_service_tracker.{external_name}"
        return self.env.ref(external_id, raise_if_not_found=False)

    vacancy_type_ids = fields.Many2many(
        string="Vacancy type",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_vacancy_type_ids(),
        help="Vacancy types included in the offer (e.g. general, disability)",
        comodel_name="civil.service.tracker.vacancy.type",
        relation="cst_quick_offer_wizard_vacancy_type_rel",
        column1="wizard_id",
        column2="vacancy_type_id",
        domain=[],
        context={},
    )

    def default_vacancy_type_ids(self):
        external_name = "civil_service_tracker_vacancy_type_general"
        external_id = f"civil_service_tracker.{external_name}"
        general = self.env.ref(external_id, raise_if_not_found=False)

        external_name = "civil_service_tracker_vacancy_type_disabilities"
        external_id = f"civil_service_tracker.{external_name}"
        disabilities = self.env.ref(external_id, raise_if_not_found=False)

        return general | disabilities

    service_position_ids = fields.Many2many(
        string="Service positions",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=(
            "Available service positions related to the selected "
            "administration"
        ),
        comodel_name="civil.service.tracker.service.position",
        relation="cst_quick_offer_wizard_service_position_rel",
        column1="wizard_id",
        column2="service_position_id",
        domain=[],
        context={},
    )

    wizard_line_ids = fields.One2many(
        string="Generated lines",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Lines automatically generated from selected filters",
        comodel_name="civil.service.tracker.quick.offer.wizard.line",
        inverse_name="wizard_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            "valid_year_list",
            "CHECK (offer_year IS NULL OR offer_year ~ '^\\s*\\d{4}\\s*(,\\s*\\d{4}\\s*)*$')",
            "Only four-digit years, separated by commas, are allowed.",
        )
    ]

    @api.constrains(
        "contract_type_ids",
        "access_type_ids",
        "selection_method_ids",
        "vacancy_type_ids",
        "service_position_ids",
        "wizard_line_ids",
    )
    def _check_required_collections(self):
        required_fields = [
            (
                "contract_type_ids",
                _("At least one contract type is required."),
            ),
            ("access_type_ids", _("At least one access type is required.")),
            (
                "selection_method_ids",
                _("At least one selection method is required."),
            ),
            ("vacancy_type_ids", _("At least one vacancy type is required.")),
            (
                "service_position_ids",
                _("At least one service position is required."),
            ),
            (
                "wizard_line_ids",
                _("At least one wizard line must be created."),
            ),
        ]
        for record in self:
            for field_name, error_message in required_fields:
                if not record[field_name]:
                    raise ValidationError(error_message)

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    def _compute_public_offer_domain(self):
        """
        Compute the domain used to filter public offers based on
        the selected public administration and offer year.

        Used in onchange methods and computed fields to restrict
        available offers (e.g., in `public_offer_id` domain or
        to compute `public_offer_count`).
        """
        domain = []

        administration = self.public_administration_id
        if administration:
            leaf = ("public_administration_id", "=", administration.id)
            domain.append(leaf)

        offer_year = self.offer_year
        if offer_year:
            leaf = ("offer_year", "=", offer_year)
            domain.append(leaf)

        return domain

    def _compute_service_position_domain(self):
        """
        Compute the domain used to filter service positions
        based on the selected public administration.

        Used by the onchange method of `public_administration_id`
        to auto-populate `service_position_ids`.
        """
        domain = FALSE_DOMAIN

        if self.public_administration_id:
            admin_id = self.public_administration_id.id
            domain = [("public_administration_id", "=", admin_id)]

        return domain

    def _build_wizard_line_commands(self):
        """
        Generator that yields all possible combinations of selected
        service positions, access types, selection methods, contract types,
        and vacancy types.

        Used by `_build_wizard_line_commands()` to generate wizard lines.
        """
        commands = [(5, 0, 0)]
        if self.state == "step3":
            for (
                position,
                access,
                selection,
                contract,
                vacancy,
            ) in self._iter_wizard_line_combinations():
                values = {
                    "service_position_id": position._origin.id,
                    "access_type_id": access._origin.id,
                    "selection_method_id": selection._origin.id,
                    "contract_type_id": contract._origin.id,
                    "vacancy_type_id": vacancy._origin.id,
                    "position_quantity": 0,
                }
                commands.append((0, 0, values))

        return commands

    def _iter_wizard_line_combinations(self):
        """
        Build the list of commands to populate the One2many field
        `wizard_line_ids` with lines representing all valid combinations.

        Triggered from the `onchange` of `state` when moving to 'step3'.
        """
        for position in self.service_position_ids:
            for access in self.access_type_ids:
                for select in self.selection_method_ids:
                    for contract in self.contract_type_ids:
                        for vacancy in self.vacancy_type_ids:
                            yield position, access, select, contract, vacancy

    # -------------------------------------------------------------------------
    # WIZARD MAIN LOGIC
    # -------------------------------------------------------------------------

    def perform_action(self):
        """
        Entry point triggered by user interaction (e.g., button click).
        Performs the batch creation logic for each wizard record and
        triggers a reload if the active model is the selection process.
        """
        for record in self:
            record._perform_action()

        process_model = "civil.service.tracker.selection.process"
        if self.env.context.get("active_model") == process_model:
            return {"type": "ir.actions.client", "tag": "reload"}

    def _perform_action(self):
        """
        Executes the core logic for creating selection processes and
        their associated vacancy records for the current wizard record.
        Intended to be called internally from `perform_action`.
        """
        Process = self.env["civil.service.tracker.selection.process"]
        Vacancy = self.env["civil.service.tracker.vacancy.position"]

        self.ensure_one()

        public_offer = self.public_offer_id or self._create_public_offer()

        for (
            position,
            contract,
            access,
            method,
            lines,
        ) in self._iter_valid_combinations():
            values = {
                "public_offer_id": public_offer._origin.id,
                "employment_group_id": position.employment_group_id._origin.id,
                "service_position_id": position._origin.id,
                "contract_type_id": contract._origin.id,
                "access_type_id": access._origin.id,
                "selection_method_id": method._origin.id,
            }
            Process.ensure_process_name(values)
            process = Process.create(values)

            grouped_by_vacancy_type = self._group_by_vacancy_type(lines)
            for vacancy_type, vlines in grouped_by_vacancy_type.items():
                for line in vlines:
                    Vacancy.create(
                        {
                            "selection_process_id": process._origin.id,
                            "vacancy_type_id": vacancy_type._origin.id,
                            "position_quantity": line.position_quantity,
                            "name": vacancy_type.name,
                        }
                    )

    def _create_public_offer(self):
        self.ensure_one()

        public_offer_obj = self.env["civil.service.tracker.public.offer"]

        if self.public_administration_id:
            administration_id = self.public_administration_id._origin.id
        else:
            administration_id = None

        if self.issuing_authority_id:
            authority_id = self.issuing_authority_id._origin.id
        else:
            authority_id = None

        values = {
            "public_administration_id": administration_id,
            "offer_year": self.offer_year,
            "issuing_authority_id": authority_id,
            "offer_date": self.offer_date,
            "bulletin_board_url": self.bulletin_board_url,
            "official_journal_url": self.official_journal_url,
        }

        public_offer = public_offer_obj.create(values)

        return public_offer

    def _iter_valid_combinations(self):
        """
        Yields valid combinations of position, contract, access and method,
        each with their corresponding non-empty wizard lines.
        Lines with zero or negative position_quantity are excluded.
        """
        seen = set()

        for line in self.wizard_line_ids:
            if line.position_quantity <= 0:
                continue  # Skip lines with no positions

            key = (
                line.service_position_id._origin.id,
                line.contract_type_id._origin.id,
                line.access_type_id._origin.id,
                line.selection_method_id._origin.id,
            )
            if key in seen:
                continue
            seen.add(key)

            # Filter again to ensure all lines in the group are valid
            lines = self.wizard_line_ids.filtered(
                lambda l: l.service_position_id._origin.id == key[0]
                and l.contract_type_id._origin.id == key[1]
                and l.access_type_id._origin.id == key[2]
                and l.selection_method_id._origin.id == key[3]
                and l.position_quantity > 0
            )
            if lines:
                yield (
                    lines[0].service_position_id,
                    lines[0].contract_type_id,
                    lines[0].access_type_id,
                    lines[0].selection_method_id,
                    lines,
                )

    def _group_by_vacancy_type(self, lines):
        """
        Group the provided wizard lines by their vacancy type.
        Used by `perform_action()` to create related vacancy records.
        """
        grouped = {}

        for line in lines:
            vt = line.vacancy_type_id
            grouped.setdefault(vt, []).append(line)

        return grouped
