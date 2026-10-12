###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from datetime import timedelta

from odoo import api, fields, models

from ..utils.datetime_utils import local_midnight_as_utc


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

    auto_signup = fields.Boolean(
        string="Auto sign up",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Automatically sign up the student upon enrolling in a training "
        "action.",
    )

    # -- Local day boundaries ----------------------------------------------------

    def local_day_bounds_to_utc(self):
        """Return the UTC boundaries of the company's current local day.

        The start is inclusive and the end is exclusive.
        Both values are naive UTC datetimes, following Odoo conventions.

        Each local midnight is converted independently to handle
        daylight-saving time changes correctly.

        Returns:
            tuple[datetime, datetime]: Start and end of the local day in UTC.
        """
        self.ensure_one()

        tz_name = self.partner_id.tz or "UTC"
        company = self.with_context(tz=tz_name)

        today = fields.Date.context_today(company)

        start_utc = local_midnight_as_utc(
            today,
            from_tz=tz_name,
        )

        end_utc = local_midnight_as_utc(
            today + timedelta(days=1),
            from_tz=tz_name,
        )

        return start_utc, end_utc
