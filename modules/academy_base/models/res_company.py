# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api

from logging import getLogger


_logger = getLogger(__name__)


class ResCompany(models.Model):
    """Extend company with academic roles.

    Adds two responsible users at company level:
    - head_of_studies_id: academic oversight
    - erp_manager_id: ERP functional supervision
    """

    _inherit = "res.company"

    head_of_studies_id = fields.Many2one(
        string="Head of Studies",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._secure_get_user_admin_id(),
        help="User responsible for academic oversight within the platform.",
        comodel_name="res.users",
        domain=[("active", "=", True), ("share", "=", False)],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    erp_manager_id = fields.Many2one(
        string="ERP Manager",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._secure_get_user_admin_id(),
        help="User responsible for functional supervision of the ERP system.",
        comodel_name="res.users",
        domain=[("active", "=", True), ("share", "=", False)],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    @api.model
    def _secure_get_user_admin_id(self):
        """Return the Admin user id if available; otherwise fallback to current user."""
        admin = self.env.ref("base.user_admin", raise_if_not_found=False)
        if admin:
            return admin.id

        return self.env.user.id
