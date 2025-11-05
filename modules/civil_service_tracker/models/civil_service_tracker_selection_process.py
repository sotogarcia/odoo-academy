# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import AND, OR, FALSE_DOMAIN
from odoo.exceptions import ValidationError
from odoo.tools.misc import str2bool

from logging import getLogger
from uuid import uuid4
from dateutil.relativedelta import relativedelta
from lxml import etree


_logger = getLogger(__name__)


class CivilServiceTrackerSelectionProcess(models.Model):
    """
    Represents a civil service selection process.

    This model holds general information about a specific selection process,
    including its name, description, and active status. It also aggregates
    the related vacancy positions and computes the total number of positions
    offered across all types.

    Example: Administrative Assistant 2025 — Internal and External calls.
    """

    _name = "civil.service.tracker.selection.process"
    _description = "Civil service tracker selection process"

    _table = "cst_selection_process"

    _rec_name = "name"
    _order = "name ASC"

    _inherit = [
        "ownership.mixin",
        "mail.thread",
        "image.mixin",
        "mail.activity.mixin",
    ]

    _rec_names_search = ["name", "short_name"]

    name = fields.Char(
        string="Process name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name or identifier of the selection process",
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
        help='Commonly used or internal short name, e.g., "C1 del Estado".',
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
        help="Additional information about this selection process (optional)",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=True,
        default=True,
        help="Enable or disable this selection process",
        tracking=True,
    )

    token = fields.Char(
        string="Token",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: str(uuid4()),
        help="Unique token used to track this public offer",
        translate=False,
        copy=False,
        tracking=True,
    )

    contract_type_id = fields.Many2one(
        string="Contract type",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Type of employment contract (e.g. civil servant, labor staff)",
        comodel_name="civil.service.tracker.contract.type",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    # - Field: access_type_id (onchange)
    # ------------------------------------------------------------------------

    access_type_id = fields.Many2one(
        string="Access type",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_access_type_id(),
        help="Type of access to the position (e.g. internal promotion)",
        comodel_name="civil.service.tracker.access.type",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    def default_access_type_id(self):
        config = self.env["ir.config_parameter"].sudo()
        param_name = "civil_service_tracker.default_access_type_id"
        value = config.get_param(param_name, None)
        return self._safe_int(value) if value else None

    # - Field: employment_group_id (onchange)
    # ------------------------------------------------------------------------

    employment_group_id = fields.Many2one(
        string="Employment group",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Employment group or category to which this position belongs",
        comodel_name="civil.service.tracker.employment.group",
        domain=FALSE_DOMAIN,
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    # - Field: selection_method_id (onchange)
    # ------------------------------------------------------------------------

    selection_method_id = fields.Many2one(
        string="Selection method",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_selection_method(),
        help="Method used to select candidates (e.g. exam, merit-based)",
        comodel_name="civil.service.tracker.selection.method",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    def default_selection_method(self):
        config = self.env["ir.config_parameter"].sudo()
        param_name = "civil_service_tracker.default_selection_method_id"
        value = config.get_param(param_name, None)
        return self._safe_int(value) if value else None

    # - Field: service_position_id (onchange)
    # ------------------------------------------------------------------------

    service_position_id = fields.Many2one(
        string="Service position",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Service position associated with this position (e.g. Legal Corps)",
        comodel_name="civil.service.tracker.service.position",
        domain=FALSE_DOMAIN,
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    @api.onchange("service_position_id")
    def _onchange_service_position_id(self):
        for record in self:
            if not record.service_position_id:
                continue

            if not record.contract_type_id:
                record.contract_type_id = (
                    record.service_position_id.contract_type_id
                )

    # - Field: public_offer_id (onchange)
    # ------------------------------------------------------------------------

    public_offer_id = fields.Many2one(
        string="Public offer",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Public offer to which this selection process belongs",
        comodel_name="civil.service.tracker.public.offer",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    @api.onchange("public_offer_id")
    def _onchange_public_offer_id(self):
        for record in self:
            if not record.public_offer_id:
                continue

            # El registro es nuevo (aún no tiene ID) o no tiene imagen propia
            new_record = not record.id or isinstance(record.id, models.NewId)
            if new_record or not record.image_1920:
                offer_image = record.public_offer_id.image_1920
                admin_image = (
                    record.public_offer_id.public_administration_id.image_1920
                )

                # Asignar la imagen de la oferta si existe, si no la de la administración
                record.image_1920 = offer_image or admin_image

    # ------------------------------------------------------------------------

    offer_date = fields.Date(
        string="Offer date",
        readonly=True,
        index=True,
        help="Date of the offer’s official approval.",
        related="public_offer_id.offer_date",
        store=True,
        tracking=True,
        copy=False,
    )

    offer_year = fields.Char(
        string="Offer year",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Year or years to which the offer applies (YYYY, YYYY,...)",
        translate=False,
        related="public_offer_id.offer_year",
        store=True,
        tracking=True,
        copy=False,
    )

    ready_date = fields.Date(
        string="Ready date",
        required=False,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.today() + relativedelta(years=1),
        help="Recommended deadline for preparation",
        tracking=True,
        copy=False,
    )

    # - Field: public_administration_id (onchange)
    # ------------------------------------------------------------------------

    public_administration_id = fields.Many2one(
        string="Public administration",
        readonly=True,
        index=True,
        help="Administration responsible for managing this selection process",
        related="public_offer_id.public_administration_id",
        store=True,
        tracking=True,
        copy=False,
    )

    available_employment_group_ids = fields.One2many(
        string="Available groups",
        readonly=True,
        related=(
            "public_administration_id."
            "employment_scheme_ids.employment_group_ids"
        ),
    )

    # ------------------------------------------------------------------------

    issuing_authority_id = fields.Many2one(
        string="Issuing authority",
        readonly=True,
        index=True,
        help="Authority that issued or published this selection process",
        related="public_offer_id.issuing_authority_id",
        store=True,
        tracking=True,
        copy=False,
    )

    vacancy_position_ids = fields.One2many(
        string="Vacancy positions",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Vacancy positions associated with this selection process",
        comodel_name="civil.service.tracker.vacancy.position",
        inverse_name="selection_process_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    process_event_ids = fields.One2many(
        string="Process events",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="civil.service.tracker.process.event",
        inverse_name="selection_process_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    # - Field: process_event_count (computedh)
    # ------------------------------------------------------------------------

    process_event_count = fields.Integer(
        string="Event count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_process_event_count",
        copy=False,
    )

    @api.depends("process_event_ids")
    def _compute_process_event_count(self):
        for record in self:
            record.process_event_count = len(record.process_event_ids)

    # - Fields will be updated from event code
    # ------------------------------------------------------------------------

    stage_id = fields.Many2one(
        string="Stage",
        required=False,
        readonly=True,
        index=True,
        default=lambda self: self.default_stage_id(),
        help="Stage that determines the kanban column for this event.",
        comodel_name="civil.service.tracker.event.type",
        domain="[('is_stage', '=', True)]",
        context={},
        ondelete="set null",
        auto_join=False,
        group_expand="_group_expand_stage_id",
        tracking=True,
        copy=False,
    )

    def default_stage_id(self):
        domain = [("is_stage", "=", True)]
        event_type_obj = self.env["civil.service.tracker.event.type"]
        return event_type_obj.search(domain, limit=1)

    @api.model
    def _group_expand_stage_id(self, stages, domain, order):
        event_type_obj = self.env["civil.service.tracker.event.type"].sudo()
        return event_type_obj.search([("is_stage", "=", True)])

    # ------------------------------------------------------------------------

    last_event_id = fields.Many2one(
        string="Last event",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="civil.service.tracker.process.event",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=False,
    )

    last_event_date = fields.Datetime(
        string="Last event date",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        copy=False,
    )

    call_date = fields.Date(
        string="Call date",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Date the process was officially announced.",
        tracking=True,
        copy=False,
    )

    resolution_date = fields.Date(
        string="Resolution date",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Date of final resolution or appointment.",
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

    @api.depends("vacancy_position_ids.position_quantity")
    def _compute_position_total(self):
        for record in self:
            vacancy_positions = record.vacancy_position_ids
            quantities = vacancy_positions.mapped("position_quantity")
            record.position_total = sum(quantities)

    @api.model
    def _search_position_total(self, operator, value):
        """
        Custom search for the computed field 'position_total'.

        - For ('=', False) → returns records with no related positions.
        - For ('!=', False) → returns records with at least one related position.
        - Otherwise, performs a HAVING SUM(...) {operator} value filter.
        """

        if operator in ("=", "!=") and not value:
            agg = "COUNT(vp.id)"
            operator = ">" if operator == "=" else "="
            value = 0
        else:
            agg = "COALESCE(SUM(vp.position_quantity), 0)"

        query = f"""
            SELECT
              sp.id
            FROM
              cst_selection_process AS sp
            LEFT JOIN cst_vacancy_position AS vp
                ON sp.id = vp.selection_process_id
            GROUP BY
              sp.id
            HAVING
              {agg} {operator} %s
        """

        self._cr.execute(query, (value,))
        matching_ids = [row[0] for row in self._cr.fetchall()]

        return [("id", "in", matching_ids)]

    # ------------------------------------------------------------------------

    salary_min = fields.Monetary(
        string="Minimum Salary",
        required=True,
        readonly=False,
        index=True,
        default=0.0,
        help="Minimum expected or planned salary",
        tracking=True,
    )

    salary_max = fields.Monetary(
        string="Maximum Salary",
        required=True,
        readonly=False,
        index=True,
        default=0.0,
        help="Maximum expected or planned salary",
        tracking=True,
    )

    currency_id = fields.Many2one(
        string="Currency",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used to display the forecast salary",
        comodel_name="res.currency",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    annual_payments = fields.Integer(
        string="Payments per Year",
        required=True,
        readonly=False,
        index=False,
        default=14,
        help=(
            "Number of salary payments per year, including extra payments "
            "if any"
        ),
        tracking=True,
    )

    access_requirements = fields.Html(
        string="Access requirements",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Minimum conditions to apply",
        translate=True,
    )

    exam_description = fields.Html(
        string="Exam",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed information about the exam",
        translate=True,
    )

    syllabus_details = fields.Html(
        string="Syllabus",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed breakdown of the syllabus or program",
        translate=True,
    )

    job_description = fields.Html(
        string="Job description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Summary of duties and responsibilities",
        translate=True,
    )

    attachment_ids = fields.Many2many(
        string="Attachments",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="",
        comodel_name="ir.attachment",
        relation="cst_selection_process_attachment_rel",
        column1="selection_process_id",
        column2="attachment_id",
        domain=[],
        context={},
    )

    process_infographics_ids = fields.Many2many(
        string="Process infographics",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Infographics showing the structure of the public exam",
        comodel_name="ir.attachment",
        relation="cst_selection_process_process_infographics_rel",
        column1="selection_process_id",
        column2="attachment_id",
        domain=[],
        context={},
        copy=False,
    )

    # - Field: process_infographics_count (computed)
    # ------------------------------------------------------------------------

    process_infographics_count = fields.Integer(
        string="Process infographics count",
        required=True,
        readonly=True,
        index=True,
        default=0,
        help="Total number of process infographics",
        compute="_compute_process_infographics_count",
        store=True,
        copy=False,
    )

    @api.depends("process_infographics_ids")
    def _compute_process_infographics_count(self):
        for record in self:
            record.process_infographics_count = len(
                record.process_infographics_ids
            )

    # ------------------------------------------------------------------------

    content_structure_ids = fields.Many2many(
        string="Content structure infographics",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Infographics showing the structure of the public exam contents",
        comodel_name="ir.attachment",
        relation="cst_selection_process_content_structure_rel",
        column1="selection_process_id",
        column2="attachment_id",
        domain=[],
        context={},
        copy=False,
    )

    # - Field: content_structure_count (computed)
    # ------------------------------------------------------------------------

    content_structure_count = fields.Integer(
        string="Content structure count",
        required=True,
        readonly=True,
        index=True,
        default=0,
        help="Total number of content structure infographics",
        compute="_compute_content_structure_count",
        store=True,
        copy=False,
    )

    @api.depends("content_structure_ids")
    def _compute_content_structure_count(self):
        for record in self:
            record.content_structure_count = len(record.content_structure_ids)

    # ------------------------------------------------------------------------

    syllabus_breakdown_ids = fields.Many2many(
        string="Syllabus breakdown",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Documents listing topics of the public exam syllabus",
        comodel_name="ir.attachment",
        relation="cst_selection_process_syllabus_breakdown_rel",
        column1="selection_process_id",
        column2="attachment_id",
        domain=[],
        context={},
        copy=False,
    )

    # - Field: syllabus_breakdown_count (computed)
    # ------------------------------------------------------------------------

    syllabus_breakdown_count = fields.Integer(
        string="Syllabus breakdown count",
        required=True,
        readonly=True,
        index=True,
        default=0,
        help="Total number of syllabus breakdown",
        compute="_compute_syllabus_breakdown_count",
        store=True,
        copy=False,
    )

    @api.depends("syllabus_breakdown_ids")
    def _compute_syllabus_breakdown_count(self):
        for record in self:
            record.syllabus_breakdown_count = len(
                record.syllabus_breakdown_ids
            )

    # ------------------------------------------------------------------------

    exam_infographics_ids = fields.Many2many(
        string="Exam infographics",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Infographics describing the exam format and phases",
        comodel_name="ir.attachment",
        relation="cst_selection_exam_infographics_rel",
        column1="selection_process_id",
        column2="attachment_id",
        domain=[],
        context={},
        copy=False,
    )

    # - Field: exam_infographics_count (computed)
    # ------------------------------------------------------------------------

    exam_infographics_count = fields.Integer(
        string="Exam infographics count",
        required=True,
        readonly=True,
        index=True,
        default=0,
        help="Total number of exam infographics",
        compute="_compute_exam_infographics_count",
        store=True,
        copy=False,
    )

    @api.depends("exam_infographics_ids")
    def _compute_exam_infographics_count(self):
        for record in self:
            record.exam_infographics_count = len(record.exam_infographics_ids)

    # ------------------------------------------------------------------------

    student_results_ids = fields.Many2many(
        string="Student results",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Reports analyzing past results (external links allowed)",
        comodel_name="ir.attachment",
        relation="cst_selection_process_student_results_rel",
        column1="selection_process_id",
        column2="attachment_id",
        domain=[],
        context={},
        copy=False,
    )

    # - Field: student_results_count (computed)
    # ------------------------------------------------------------------------

    student_results_count = fields.Integer(
        string="Student results count",
        required=True,
        readonly=True,
        index=True,
        default=0,
        help="Total number of student results",
        compute="_compute_student_results_count",
        store=True,
        copy=False,
    )

    @api.depends("student_results_ids")
    def _compute_student_results_count(self):
        for record in self:
            record.student_results_count = len(record.student_results_ids)

    # ------------------------------------------------------------------------

    dossier_summary = fields.Char(
        string="Dossier summary",
        required=True,
        readonly=True,
        index=False,
        default="0 / 0 / 0 / 0 / 0",
        help=False,
        translate=False,
        compute="_compute_dossier_summary",
        store=True,
        tracking=True,
        copy=False,
    )

    @api.depends(
        "process_infographics_count",
        "syllabus_breakdown_count",
        "exam_infographics_count",
        "student_results_count",
        "content_structure_count",
    )
    def _compute_dossier_summary(self):
        for record in self:
            record._compute_process_infographics_count()
            record._compute_content_structure_count()
            record._compute_exam_infographics_count()
            record._compute_syllabus_breakdown_count()
            record._compute_student_results_count()

            record.dossier_summary = "{} / {} / {} / {} / {}".format(
                record.process_infographics_count,
                record.content_structure_count,
                record.exam_infographics_count,
                record.syllabus_breakdown_count,
                record.student_results_count,
            )

    # - Field: aggregated_attachment_ids (computed)
    # ------------------------------------------------------------------------

    aggregated_attachment_ids = fields.Many2many(
        string="Aggregated attachments",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=(
            "Combined list of all documents attached to this selection "
            "process and its events."
        ),
        comodel_name="ir.attachment",
        relation="cst_selection_process_aggregated_attachment_rel",
        column1="selection_process_id",
        column2="attachment_id",
        domain=[],
        context={},
        compute="_compute_aggregated_attachment_ids",
        copy=False,
    )

    @api.depends(
        "process_infographics_ids",
        "syllabus_breakdown_ids",
        "exam_infographics_ids",
        "student_results_ids",
        "process_event_ids.attachment_id",
        "attachment_ids",
    )
    def _compute_aggregated_attachment_ids(self):
        for record in self:
            aggregated_set = self.env["ir.attachment"]

            aggregated_set |= record.attachment_ids

            aggregated_set |= record.process_infographics_ids
            aggregated_set |= record.syllabus_breakdown_ids
            aggregated_set |= record.exam_infographics_ids
            aggregated_set |= record.student_results_ids

            path = "process_event_ids.attachment_id"
            aggregated_set |= record.mapped(path)

            record.aggregated_attachment_ids = aggregated_set

    # - Field: current_company_id (computed)
    # ------------------------------------------------------------------------

    current_company_id = fields.Many2one(
        string="Current company (context)",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="res.company",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        store=False,
        compute="_compute_current_company_id",
        copy=False,
    )

    @api.depends_context("company_id")
    def _compute_current_company_id(self):
        default_company = self.env["res.company"].search([], limit=1)
        for record in self:
            record.current_company_id = (
                self.env.company or self.env.user.company_id or default_company
            )

    # - Field: is_followed_by_user (computed + search)
    # ------------------------------------------------------------------------

    is_followed_by_user = fields.Boolean(
        string="Is followed by user",
        required=False,
        readonly=True,
        index=False,
        default=False,
        help="Indicates whether the current user is following this record.",
        compute="_compute_is_followed_by_user",
        search="_search_is_followed_by_user",
        store=False,
    )

    @api.depends("message_follower_ids.partner_id")
    def _compute_is_followed_by_user(self):
        partner = self.env.user.partner_id

        for record in self:
            following_set = record.message_follower_ids.mapped("partner_id")
            record.is_followed_by_user = partner in following_set

    @api.model
    def _search_is_followed_by_user(self, operator, value):
        """Allow filtering by follow status in search views"""
        if operator not in ("=", "!="):
            message = _("Unsupported operator for is_followed_by_user")
            raise ValueError(message)

        partner_id = self.env.user.partner_id.id

        # Encuentra todos los registros seguidos por el partner actual
        domain = [
            ("res_model", "=", self._name),
            ("partner_id", "=", partner_id),
        ]
        followed = self.env["mail.followers"].search(domain).mapped("res_id")

        condition_equal_true = value is True and operator == "="
        condition_not_equal_false = value is False and operator == "!="
        if condition_equal_true or condition_not_equal_false:
            return [("id", "in", followed)]
        else:
            return [("id", "not in", followed)]

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            "unique_selection_process_name",
            "UNIQUE(name)",
            "The name of the selection process must be unique.",
        ),
        # (
        #     "check_name_min_length",
        #     "CHECK(char_length(name) > 3)",
        #     "The name must have more than 3 characters.",
        # ),
        (
            "unique_selection_process_short_name",
            "UNIQUE(short_name)",
            "The short name of the selection process must be unique.",
        ),
        # (
        #     "check_short_name_min_length",
        #     "CHECK(char_length(name) > 3)",
        #     "The short name must have more than 3 characters.",
        # ),
        (
            "unique_selection_process_token",
            "UNIQUE(token)",
            "The token must be unique.",
        ),
        (
            "check_salary_range",
            "CHECK(salary_min <= salary_max)",
            "Minimum must be less than or equal to maximum",
        ),
        (
            "check_salary_non_negative",
            "CHECK(salary_min >= 0 AND salary_max >= 0)",
            "Salary values must be greater than or equal to zero",
        ),
    ]

    @api.constrains("public_administration_id", "employment_group_id")
    def _check_employment_group_consistency(self):
        """Employment Group must be allowed by the chosen Public
        Administration. Fail-fast with per-admin lazy cache."""

        records = self.filtered(
            lambda r: r.public_administration_id and r.employment_group_id
        )
        if not records:
            return

        group_path = "employment_scheme_ids.employment_group_ids"
        allowed_by_admin = {}

        for record in records:
            admin = record.public_administration_id
            allowed = allowed_by_admin.get(admin.id)
            if allowed is None:
                allowed = set(admin.mapped(group_path).ids)
                allowed_by_admin[admin.id] = allowed

            if record.employment_group_id.id not in allowed:
                message = _(
                    "The selected Employment Group is not allowed by the "
                    "chosen Public Administration."
                )
                raise ValidationError(message)

    @api.constrains(
        "service_position_id",
        "employment_group_id",
        "public_administration_id",
    )
    def _check_service_position_consistency(self):
        # Mensaje base para el error
        message = _(
            "The '{fs}' of the selected Service Position must match "
            "the '{fs}' of the Selection Process."
        )

        for record in self:
            if not record.service_position_id:
                continue  # No requiere validación, pero no debería darse

            position_record = record.service_position_id

            # --- Employment Group validation ---
            field_name = "employment_group_id"
            field_string = self._fields[field_name].string
            if not record._match_field(position_record, field_name):
                raise ValidationError(message.format(fs=field_string))

            # --- Public Administration validation ---
            field_name = "public_administration_id"
            field_string = self._fields[field_name].string
            if not record._match_field(position_record, field_name):
                raise ValidationError(message.format(fs=field_string))

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

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        for values in values_list:
            self.ensure_process_name(values)

        parent = super(CivilServiceTrackerSelectionProcess, self)
        result = parent.create(values_list)

        targets = result.filtered(lambda record: record.public_offer_id)
        if targets:
            targets.synchronize_offer_approval_event()

        return result

    def write(self, values):
        """Overridden method 'write'"""

        parent = super(CivilServiceTrackerSelectionProcess, self)
        result = parent.write(values)

        if "public_offer_id" in values:
            self.synchronize_offer_approval_event()

        return result

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """Prevents new record of the inherited (_inherits) model will be
        created
        """

        new_name = self.env.context.get("default_name", False)
        if not new_name:
            new_name = f"{self.name} - {str(uuid4())[-12:]}"

        default = dict(default or {})
        default.update({"name": new_name})

        parent = super(CivilServiceTrackerSelectionProcess, self)
        result = parent.copy(default)

        return result

    # fields_view_get, _dossier_company_domains, _dossier_non_empty_domains
    # -------------------------------------------------------------------------

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """
        Overrides the base method to dynamically inject domain filters into
        the search view.

        This method adjusts the 'complete_dossier' and 'incomplete_dossier'
        filter nodes in the search view XML to reflect the currently selected
        companies in a multi-company environment.
        The domains are generated to check whether the dossier fields have
        attachments linked to the active companies (or not), ensuring accurate
        filtering per user's company context.

        :param view_id: Optional ID of the view to retrieve.
        :param view_type: Type of the view ('form', 'tree', 'search', etc.).
        :param toolbar: Whether to include toolbar actions.
        :param submenu: Whether to include submenu actions.
        :return: view definition with modified domain filters if search view.
        """
        parent = super(CivilServiceTrackerSelectionProcess, self)
        result = parent.fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type != "search":
            return result

        doc = etree.XML(result["arch"])
        active_company_ids = set(self.env.companies.ids)

        dossier_fields = [
            "process_infographics_ids",
            "content_structure_ids",
            "exam_infographics_ids",
            "syllabus_breakdown_ids",
            "student_results_ids",
        ]

        for node in doc.xpath("//filter[@name='complete_dossier']"):
            domains = self._dossier_company_domains(
                dossier_fields, active_company_ids, "="
            )
            domain = AND(domains) if domains else FALSE_DOMAIN
            node.set("domain", str(domain))

        for node in doc.xpath("//filter[@name='incomplete_dossier']"):
            domains = self._dossier_company_domains(
                dossier_fields, active_company_ids, "!="
            )

            if domains:
                non_empty = self._dossier_non_empty_domains(dossier_fields)
                domains.extend(non_empty)
                domain = OR(domains)
            else:
                domain = FALSE_DOMAIN

            node.set("domain", str(domain))

        result["arch"] = etree.tostring(doc, encoding="unicode")

        return result

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def _dossier_company_domains(dossier_fields, active_company_ids, operator):
        """
        Builds a list of domains to compare each dossier field's company_id
        with a set of company IDs using the provided operator.
        """
        domains = []

        for company_id in active_company_ids:
            for field_name in dossier_fields:
                left_part = f"{field_name}.company_id"
                domain = [(left_part, operator, company_id)]
                domains.append(domain)

        return domains

    @staticmethod
    def _dossier_non_empty_domains(dossier_fields):
        """
        Builds a list of domain expressions to check if the dossier fields are
        empty.
        """
        domains = []

        for field_name in dossier_fields:
            domain = [(field_name, "=", False)]
            domains.append(domain)

        return domains

    def _match_field(self, target_record, field_name):
        self_value = getattr(self, field_name)
        target_value = getattr(target_record, field_name)

        if not self_value and not target_value:
            return True

        return self_value == target_value

    @api.model
    def ensure_process_name(self, values):
        values = values or {}

        name = values.get("name", None)
        if name:
            return

        position_id = values.get("service_position_id", None)
        position_obj = self.env["civil.service.tracker.service.position"]
        position = position_obj.browse(position_id)
        if not position:
            return

        group_id = values.get("employment_group_id", None)
        group_obj = self.env["civil.service.tracker.employment.group"]
        group = group_obj.browse(group_id)
        if not group:
            return

        offer_id = values.get("public_offer_id", None)
        offer_obj = self.env["civil.service.tracker.public.offer"]
        offer = offer_obj.browse(offer_id)
        if not offer:
            return

        access_id = values.get("access_type_id", None)
        access_obj = self.env["civil.service.tracker.access.type"]
        access = access_obj.browse(access_id)
        if not access:
            return

        values[
            "name"
        ] = f"{position.name} ({group.name}) — {offer.name}, {access.name}"

        if position.short_name and offer.short_name:
            values["short_name"] = (
                f"{position.short_name} ({group.name}) — "
                f"{offer.short_name}, {access.name}"
            )

        return name

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(value)
        except (ValueError, TypeError):
            _logger.warning(f"Method _safe_int could not convert {value}")
            return default

    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value

        if value is None:
            return False

        return str(value).strip().lower() in ("1", "true", "yes", "on")

    @api.model
    def _get_value_for_field(self, events, field_name):
        result = None

        # Search for target field
        module = "civil_service_tracker"
        name = f"field_civil_service_tracker_selection_process__{field_name}"
        field = self.env.ref(f"{module}.{name}", raise_if_not_found=False)

        # Search for an event which type it's related with target field
        if field:
            event = events.filtered(
                lambda ev: ev.event_type_id.related_field_id.id == field.id
            )
            if event:
                result = event[0].event_date

        return result

    def _update_event_values(self, values):
        self.ensure_one()

        events = self.process_event_ids
        if events:
            # Sort events, newerest first
            events = events.sorted(key="event_date", reverse=True)

            # Update last_event_id and last_event_date
            values["last_event_id"] = events[0].id
            values["last_event_date"] = events[0].event_date

            # Update call_date and resolution_date
            for field_name in ["call_date", "resolution_date"]:
                value = self._get_value_for_field(events, field_name)
                values[field_name] = value

            # Update stage_id
            stages = events.filtered(lambda ev: ev.event_type_id.is_stage)
            stages.sorted(key="event_date", reverse=False)
            if stages:
                event = stages.sorted(key="event_date", reverse=True)[0]
                values["stage_id"] = event.event_type_id.id

    def _update_approval_event(self, event_type, offer):
        """Update or create the approval event for the process."""
        self.ensure_one()

        existing = self.process_event_ids.filtered(
            lambda ev: ev.event_type_id.id == event_type.id
        )
        event = existing[0] if existing else None

        description = _(
            "The public employment offer for the year %s has been published."
        ) % (offer.offer_year)

        event_values = {
            "name": event.name if event else event_type.name,
            "description": description,
            "active": True,
            "selection_process_id": self.id,
            "issuer_partner_id": offer.public_administration_id.partner_id.id,
            "event_type_id": event_type.id,
            "event_date": offer.offer_date,
        }

        if event:
            event.write(event_values)
        else:
            event_obj = self.env["civil.service.tracker.process.event"]
            event = event_obj.create(event_values)

        return event

    def _attach_approval_event_journal_url(self, event, journal_url):
        """Attach or update a URL attachment for the given event."""
        self.ensure_one()
        attachment = event.attachment_id

        attachment_values = {
            "type": "url",
            "url": journal_url,
            "res_model": "civil.service.tracker.process.event",
            "res_id": event.id,
        }

        if attachment:
            # TODO: (Patch) Problemas con public=True
            attachment.sudo().write(attachment_values)
        else:
            attachment_values["name"] = _("Link to official document")
            event.attachment_id = self.env["ir.attachment"].create(
                attachment_values
            )

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def refresh_event_information(self):
        """
        Recompute and update event-related fields for each selection process.

        This method resets and recalculates key event data fields based on the
        current state of associated events. It determines the default stage,
        clears and prepares fields like last event reference and dates, and
        then writes the updated values to the process record.

        Fields affected:
            - stage_id
            - last_event_id
            - last_event_date
            - call_date
            - resolution_date

        Used when events have been added, modified, or removed and the
        selection process needs to reflect the new state.
        """

        for record in self:
            values = {
                "stage_id": record.default_stage_id(),
                "last_event_id": None,
                "last_event_date": None,
                "call_date": None,
                "resolution_date": None,
            }

            message = "Refresh %s(%s) event information with values: %s"
            _logger.debug(message, record._name, record.id, values)

            record._update_event_values(values)
            record.write(values)

    def synchronize_offer_approval_event(self):
        """Create or update the offer approval event and link the official
        journal URL if available.
        """

        external_id = "civil_service_tracker.cst_event_type_offer_approval"
        try:
            event_type = self.env.ref(external_id)
        except ValueError:
            raise ValidationError(_("Missing event type: %s") % external_id)

        for record in self:
            offer = record.public_offer_id
            year = offer.offer_year
            offer_date = offer.offer_date

            _logger.debug(
                "Synchronizing offer approval event for process %s (%s)",
                record.id,
                record.name,
            )
            event = record._update_approval_event(event_type, offer)

            journal_url = offer.official_journal_url
            if journal_url:
                _logger.debug("Attaching journal URL to event %s", event.id)
                record._attach_approval_event_journal_url(event, journal_url)

    def refresh_dossier_summary(self):
        self._compute_dossier_summary()

    def action_view_selection_process_details(self):
        self.ensure_one()

        url = f"/civil-service-tracker/web/selection-process/item/{self.token}"

        return {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": url,
            "target": "new",
        }
