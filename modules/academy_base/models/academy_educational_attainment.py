###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import fields, models


class AcademyEducationalAttainment(models.Model):
    """Represent an educational attainment level."""

    _name = "academy.educational.attainment"
    _description = "Academy educational attainment"

    _rec_name = "name"
    _order = "sequence ASC, name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the educational attainment",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the educational attainment",
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

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Choose educational attainment order",
    )

    level = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official ISCED educational attainment code",
        size=8,
        translate=False,
    )

    # -- SQL constraints ------------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "level_unique",
            "unique(level)",
            "Educational attainment code must be unique.",
        ),
    ]
