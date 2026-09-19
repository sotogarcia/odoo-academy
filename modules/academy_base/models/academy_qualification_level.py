###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from odoo import fields, models


class AcademyQualificationLevel(models.Model):
    """Qualification level is a property of the training program."""

    _name = "academy.qualification.level"
    _description = "Academy qualification level"

    _rec_name = "name"
    _rec_names_search = ["name", "level"]  # noqa: RUF012
    _order = "sequence ASC, name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Qualification Level",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Qualification Level",
        translate=True,
    )

    level = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official qualification level code",
        size=8,
        translate=False,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Choose level order",
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
    )

    # -- SQL constraints ------------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "level_unique",
            "unique(level)",
            "Qualification level code must be unique.",
        ),
    ]
