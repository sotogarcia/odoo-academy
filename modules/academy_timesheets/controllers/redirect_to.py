# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.http import Controller, request, route
from odoo.tools.translate import _

from logging import getLogger
from urllib.parse import urljoin
import werkzeug.utils

_logger = getLogger(__name__)

WND_URL = "/web#action={action}&model={model}&view_type={view}"

FACILITIES_WIZARD_URL = "/academy_timesheets/redirect/facilities"
TEACHERS_WIZARD_URL = "/academy_timesheets/redirect/teachers"


class RedirectTo(Controller):
    """Redirects to internal views

    Routes:
      /some_url: url description
    """

    @staticmethod
    def _tree_to_list(view_modes):
        if isinstance(view_modes, str):
            view_modes = view_modes.split(",")

        if "list" in view_modes:
            view_modes[view_modes.index("list")] = "list"

        return view_modes

    @staticmethod
    def _base_url():
        param_obj = request.env["ir.config_parameter"].sudo()
        return param_obj.get_param("web.base.url")

    def _act_window_to_url(self, action, view_type="list"):
        if isinstance(action, str):
            action = request.env.ref(action)

        view_modes = self._tree_to_list(action.view_mode)
        assert view_type in view_modes, _(
            'Invalid view type for action "%s"' % action.name
        )

        action_id = action.id
        model = action.res_model

        return WND_URL.format(action=action_id, model=model, view=view_type)

    @route(FACILITIES_WIZARD_URL, type="http", auth="user", website=False)
    def facilities_url(self, **kw):
        action_xid = "facility_management." "action_facilities_act_window"

        base_url = self._base_url()
        relative_url = self._act_window_to_url(action_xid, view_type="kanban")
        full_url = urljoin(base_url, relative_url)

        return werkzeug.utils.redirect(full_url)

    @route(TEACHERS_WIZARD_URL, type="http", auth="user", website=False)
    def teachers_url(self, **kw):
        action_xid = "academy_base." "action_teacher_act_window"

        base_url = self._base_url()
        relative_url = self._act_window_to_url(action_xid, view_type="kanban")
        full_url = urljoin(base_url, relative_url)

        return werkzeug.utils.redirect(full_url)
