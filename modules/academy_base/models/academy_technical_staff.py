###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, models


class AcademyTechnicalStaff(models.Model):
    """A technical staff member is a specialized support staff member."""

    _name = "academy.technical.staff"
    _description = "Academy technical staff member"

    _inherit = [  # noqa: RUF012
        "academy.support.staff",
    ]

    _order = "complete_name ASC, id DESC"

    _rec_name = "complete_name"
    _rec_names_search = [  # noqa: RUF012
        "complete_name",
        "email",
        "vat",
        "company_registry",
    ]

    # -- Methods overrides ----------------------------------------------------

    @api.model
    def _get_relevant_category_external_id(self):
        return "academy_base.res_partner_category_technical_staff"
