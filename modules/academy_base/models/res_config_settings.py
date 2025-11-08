# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Module configuration attributes"""

    _inherit = ["res.config.settings"]

    head_of_studies_id = fields.Many2one(
        string="Head of Studies",
        required=True,
        readonly=False,
        help="User responsible for academic oversight within the platform.",
        related="company_id.head_of_studies_id",
    )

    erp_manager_id = fields.Many2one(
        string="ERP Manager",
        required=True,
        readonly=False,
        help="User responsible for functional supervision of the ERP system.",
        related="company_id.erp_manager_id",
    )

    partner_email_required = fields.Selection(
        string="Require email for partners",
        required=True,
        readonly=False,
        index=False,
        default="except_debug",
        help=(
            "Control when email address is mandatory: never, always, or "
            "except when developer mode is active."
        ),
        selection=[
            ("never", "Never"),
            ("always", "Always"),
            ("except_debug", "Except in developer mode"),
        ],
        config_parameter="academy_base.partner_email_required",
    )

    partner_vat_required = fields.Selection(
        string="Require VAT for partners",
        required=True,
        readonly=False,
        index=False,
        default="except_debug",
        help=(
            "Control when VAT number is mandatory: never, always, or "
            "except when developer mode is active."
        ),
        selection=[
            ("never", "Never"),
            ("always", "Always"),
            ("except_debug", "Except in developer mode"),
        ],
        config_parameter="academy_base.partner_vat_required",
    )
