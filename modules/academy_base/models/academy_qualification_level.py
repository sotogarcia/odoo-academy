###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from odoo import fields, models


class AcademyQualificationLevel(models.Model):
    """Professional qualification levels used by training programmes and qualifications."""

    _name = "academy.qualification.level"
    _description = "Academy qualification level"

    _rec_name = "name"
    _rec_names_search = ["name", "code"]  # noqa: RUF012
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
        help="Detailed description of the qualification Level",
        translate=True,
    )

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Professional qualification level code (1 to 5).",
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
            "unique(code)",
            "Qualification level code must be unique.",
        ),
    ]
