###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from logging import getLogger

from odoo import fields, models

_logger = getLogger(__name__)


class AcademyProfessionalField(models.Model):
    """Professional field is a property of the training program"""

    _name = "academy.professional.field"
    _description = "Academy professional field"

    _inherit = ["image.mixin"]  # noqa: RUF012

    _rec_names_search = ["name", "code"]  # noqa: RUF012
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Field",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Field",
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

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new code",
        size=8,
        translate=False,
    )

    professional_sector_ids = fields.One2many(
        string="Professional sectors",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="List of sectors related to this professional field.",
        comodel_name="academy.professional.sector",
        inverse_name="professional_field_id",
        domain=[],
        context={},
        auto_join=False,
    )

    _sql_constraints = [  # noqa: RUF012
        (
            "code_unique",
            "unique(code)",
            "Professional field code must be unique.",
        ),
    ]
