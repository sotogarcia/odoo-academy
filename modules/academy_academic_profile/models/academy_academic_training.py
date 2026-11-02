###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import fields, models


class AcademyAcademicTraining(models.Model):
    """Catalogue of academic and vocational training qualifications."""

    _name = "academy.academic.training"
    _description = "Academic training"

    _rec_name = "name"
    _order = "name ASC"

    # -- Fields ---------------------------------------------------------------

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name of the academic or vocational training qualification.",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
    )

    attainment_id = fields.Many2one(
        string="Educational attainment",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Educational attainment level associated with this training.",
        comodel_name="education.classification.item",
        domain=[("dimension", "=", "a")],
        context={"search_default_group_by_edition_id": 1},
        ondelete="set null",
        auto_join=False,
    )

    field_id = fields.Many2one(
        string="Field of study",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Field of education or training associated with this qualification.",
        comodel_name="education.classification.item",
        domain=[("dimension", "=", "f")],
        context={"search_default_group_by_edition_id": 1},
        ondelete="set null",
        auto_join=False,
    )

    program_id = fields.Many2one(
        string="Educational program",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Educational program or course type associated with this training.",
        comodel_name="education.classification.item",
        domain=[("dimension", "=", "p")],
        context={"search_default_group_by_edition_id": 1},
        ondelete="set null",
        auto_join=False,
    )

    edition_id = fields.Many2one(
        string="Edition",
        help="Classification edition to which this category belongs.",
        comodel_name="education.classification.edition",
        related="attainment_id.edition_id",
        store=True,
    )
