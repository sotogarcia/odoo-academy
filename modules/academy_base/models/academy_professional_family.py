###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from odoo import api, fields, models

from ..utils.helpers import (
    one2many_count,
    one2many_count_search_domain,
)


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalFamily(models.Model):
    """Professional family is a property of the training program"""

    _name = "academy.professional.family"
    _description = "Academy professional family"

    _inherit = ["image.mixin"]  # noqa: RUF012

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Family",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Family",
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

    professional_area_ids = fields.One2many(
        string="Professional area",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.professional.area",
        inverse_name="professional_family_id",
        domain=[],
        context={},
        auto_join=False,
    )

    professional_qualification_ids = fields.One2many(
        string="Professional qualifications",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.professional.qualification",
        inverse_name="professional_family_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    # pylint: disable=locally-disabled, W0212
    professional_area_count = fields.Integer(
        string="No. of areas",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=(
            "Shows the number of professional areas that belong to this "
            "family"
        ),
        compute="_compute_professional_area_count",
        search="_search_professional_area_count",
    )

    @api.depends("professional_area_ids")
    def _compute_professional_area_count(self):
        counts = one2many_count(self, "professional_area_ids")

        for record in self:
            record.professional_area_count = counts.get(record.id, 0)

    @api.model
    def _search_professional_area_count(self, operator, value):
        return one2many_count_search_domain(
            self,
            "professional_area_ids",
            operator,
            value,
        )
