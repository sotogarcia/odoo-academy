###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from odoo import fields, models


class AcademyProfessionalSector(models.Model):
    """Professional sector is a property of the training program"""

    _name = "academy.professional.sector"
    _description = "Academy professional sector"

    _inherit = ["image.mixin"]  # noqa: RUF012

    _rec_names_search = ["name", "code"]  # noqa: RUF012
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Sector",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Sector",
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

    professional_field_id = fields.Many2one(
        string="Professional field",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional field",
        comodel_name="academy.professional.field",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    _sql_constraints = [  # noqa: RUF012
        (
            "code_unique",
            "unique(code)",
            "Professional sector code must be unique.",
        ),
    ]
