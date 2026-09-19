###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalQualification(models.Model):
    """Professional qualification is a property of the training program"""

    _name = "academy.professional.qualification"
    _description = "Academy professional qualification"

    _inherit = ["image.mixin"]  # noqa: RUF012

    _rec_names_search = [  # noqa: RUF012
        "name",
        "qualification_code",
    ]
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Qualification",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Qualification",
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

    professional_family_id = fields.Many2one(
        string="Professional family",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional family",
        comodel_name="academy.professional.family",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.onchange("professional_family_id")
    def _onchange_professional_family_id(self):
        self.professional_area_id = None

    professional_area_id = fields.Many2one(
        string="Professional area",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional area",
        comodel_name="academy.professional.area",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    qualification_code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Enter new internal code",
        size=30,
        translate=False,
    )

    qualification_level_id = fields.Many2one(
        string="Qualification level",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related qualification level",
        comodel_name="academy.qualification.level",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.constrains("professional_family_id", "professional_area_id")
    def _check_professional_area_id(self):
        message1 = _("Select a professional family before choosing an area.")
        message2 = _("Area %s does not belong to family %s.")

        for record in self:
            area = record.professional_area_id

            if not area:
                continue

            family = record.professional_family_id

            if not family:
                raise ValidationError(message1)

            if area.professional_family_id != family:
                raise ValidationError(
                    message2
                    % (
                        area.display_name,
                        family.display_name,
                    )
                )
