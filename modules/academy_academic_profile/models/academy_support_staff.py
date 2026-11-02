###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models


class AcademySupportStaff(models.Model):
    """Extend support staff with academic qualifications."""

    _inherit = "academy.support.staff"

    # -- Fields ---------------------------------------------------------------

    attainment_id = fields.Many2one(
        string="Educational attainment",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Highest level of education attained.",
        comodel_name="education.classification.item",
        domain=[("dimension", "=", "a")],
        context={"search_default_group_by_edition_id": 1},
        ondelete="set null",
        auto_join=False,
        tracking=True,
    )

    academic_training_ids = fields.Many2many(
        string="Academic training",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Academic and vocational training qualifications held by this person.",
        comodel_name="academy.academic.training",
        column1="person_id",
        column2="academic_training_id",
        domain=[],
        context={},
    )

    cefrl_ids = fields.Many2many(
        string="Languages",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Language certificates held by this person.",
        comodel_name="cefrl.certificate",
        column1="person_id",
        column2="certificate_id",
        domain=[],
        context={},
    )

    driving_licence_ids = fields.Many2many(
        string="Driving licences",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Driving licences held by this person.",
        comodel_name="driving.licence",
        column1="person_id",
        column2="driving_licence_id",
        domain=[],
        context={},
    )

    # -- Computed field: implied_cefrl_ids ------------------------------------

    implied_cefrl_ids = fields.Many2many(
        string="Implied languages",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Directly held and implied language certificates.",
        comodel_name="cefrl.certificate",
        domain=[],
        context={},
        compute="_compute_implied_cefrl_ids",
    )

    @api.depends("cefrl_ids", "cefrl_ids.implied_ids")
    def _compute_implied_cefrl_ids(self):
        for record in self:
            record.implied_cefrl_ids = (
                record.cefrl_ids | record.cefrl_ids.implied_ids
            )

    # -- Computed field: implied_driving_licence_ids --------------------------

    implied_driving_licence_ids = fields.Many2many(
        string="Implied driving licences",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Directly held and implied driving licences.",
        comodel_name="driving.licence",
        domain=[],
        context={},
        compute="_compute_implied_driving_licence_ids",
    )

    @api.depends("driving_licence_ids", "driving_licence_ids.implied_ids")
    def _compute_implied_driving_licence_ids(self):
        for record in self:
            record.implied_driving_licence_ids = (
                record.driving_licence_ids
                | record.driving_licence_ids.implied_ids
            )

    # -- Computed field: highest_attainment_id -------------------------------

    highest_attainment_id = fields.Many2one(
        string="Highest attainment",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Highest educational attainment level among the person's "
        "registered academic training qualifications.",
        comodel_name="education.classification.item",
        domain=[("dimension", "=", "a")],
        context={"search_default_group_by_edition_id": 1},
        ondelete="set null",
        auto_join=False,
        compute="_compute_highest_attainment_id",
    )

    @api.depends(
        "academic_training_ids",
        "academic_training_ids.attainment_id",
        "academic_training_ids.attainment_id.weight",
    )
    def _compute_highest_attainment_id(self):
        for record in self:
            attainments = record.academic_training_ids.mapped("attainment_id")
            attainments = attainments.filtered(lambda item: item.weight > 0)

            record.highest_attainment_id = (
                max(attainments, key=lambda item: (item.weight, item.id))
                if attainments
                else False
            )

    # -- Computed field: attainment_status ------------------------------------

    attainment_status = fields.Selection(
        string="Attainment status",
        required=False,
        readonly=True,
        index=False,
        default=False,
        help="Consistency between declared and calculated educational attainment.",
        compute="_compute_attainment_status",
        selection=[
            ("undetermined", "Undetermined"),
            ("consistent", "Consistent"),
            ("different", "Different"),
        ],
    )

    @api.depends(
        "attainment_id",
        "attainment_id.weight",
        "highest_attainment_id",
        "highest_attainment_id.weight",
    )
    def _compute_attainment_status(self):
        for record in self:
            declared = record.attainment_id
            highest = record.highest_attainment_id

            if not record.academic_training_ids:
                record.attainment_status = False

            elif not declared or not highest:  # noqa: SIM114
                record.attainment_status = "undetermined"

            elif declared.weight <= 0:
                record.attainment_status = "undetermined"

            elif declared.weight == highest.weight:
                record.attainment_status = "consistent"

            else:
                record.attainment_status = "different"
