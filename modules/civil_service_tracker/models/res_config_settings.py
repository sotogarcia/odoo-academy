# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Module configuration attributes"""

    _inherit = ["res.config.settings"]

    display_process_short_name = fields.Boolean(
        string="Use short name",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Show short name in selection process displays",
        config_parameter="civil_service_tracker.display_process_short_name",
    )

    main_act_window_id = fields.Many2one(
        string="Main window",
        required=True,
        readonly=False,
        index=False,
        default=None,  # El default será manejado por get_values
        help="Main window associated with civil service tracker menu",
        comodel_name="ir.actions.act_window",
        domain=[("target", "in", ["current", "main"])],
        context={},
        ondelete="cascade",
        auto_join=False,
        store=True,
    )

    access_type_id = fields.Many2one(
        string="Default access type",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Type of access to the position (e.g. internal promotion)",
        comodel_name="civil.service.tracker.access.type",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        config_parameter="civil_service_tracker.default_access_type_id",
    )

    selection_method_id = fields.Many2one(
        string="Default selection method",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Method used to select candidates (e.g. exam, merit-based)",
        comodel_name="civil.service.tracker.selection.method",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        config_parameter="civil_service_tracker.default_selection_method_id",
    )

    tracking_responsible_id = fields.Many2one(
        string="Selection Process Supervisor",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.env.ref("base.user_admin"),
        help=(
            "Person responsible for supervising civil service selection "
            "processes"
        ),
        comodel_name="res.users",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
        config_parameter="civil_service_tracker.tracking_responsible_id",
    )

    erp_manager_id = fields.Many2one(
        string="ERP Manager",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.env.ref("base.user_admin"),
        help=(
            "Person in charge of maintaining the civil service tracker "
            "module"
        ),
        comodel_name="res.users",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
        config_parameter="civil_service_tracker.erp_manager_id_id",
    )

    def set_values(self):
        super().set_values()

        # --- main_act_window_id --
        xid = "civil_service_tracker.menu_civil_service_tracker_root"
        menu = self.env.ref(xid, raise_if_not_found=False)
        if menu and self.main_act_window_id:
            menu.write(
                {
                    "action": f"ir.actions.act_window,{self.main_act_window_id.id}"
                }
            )

    def get_values(self):
        result = super().get_values()

        # --- main_act_window_id --
        xid = "civil_service_tracker.menu_civil_service_tracker_root"
        menu = self.env.ref(xid, raise_if_not_found=False)
        act_window = False

        if menu and menu.action:
            if isinstance(menu.action, str):
                model, action_id = menu.action.split(",")
                if model == "ir.actions.act_window":
                    act_window = self.env["ir.actions.act_window"].browse(
                        int(action_id)
                    )
            elif isinstance(menu.action, models.BaseModel):
                act_window = menu.action

        result["main_act_window_id"] = act_window.id if act_window else False

        return result
