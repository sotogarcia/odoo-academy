###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from odoo import fields, models


class AcademyKnowledgeArea(models.Model):
    """Knowledge area is a property of the training action"""

    _name = "academy.knowledge.area"
    _description = "Academy knowledge area"

    _rec_names_search = ["name", "knowle_code"]  # noqa: RUF012
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Knowledge Area",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Knowledge Area",
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

    knowle_code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new code",
        size=30,
        translate=False,
    )

    _sql_constraints = [  # noqa: RUF012
        (
            "code_unique",
            "unique(knowle_code)",
            "Knowledge area code must be unique.",
        ),
    ]
