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


IMPUGNMENTS_URL = '/academy_tests/redirect/impugnments'
WND_URL = '/web#action={action}&model={model}&view_type={view}&menu_id={menu}'


class RedirectTo(Controller):
    """ Allows to redirect users to an internal URLs, like tree views, etc...

        Routes:
          /some_url: url description
    """

    @staticmethod
    def _base_url():
        param_obj = request.env["ir.config_parameter"].sudo()
        return param_obj.get_param("web.base.url")

    @staticmethod
    def _menu_to_url(menu, view_type='list'):
        if isinstance(menu, str):
            menu = request.env.ref(menu)

        action_obj = request.env['ir.actions.act_window']
        assert menu.action and isinstance(menu.action, type(action_obj)), \
            _('The menu item must have an associated window action')

        assert view_type in menu.action.view_mode.split(','), \
            _('Invalid view type for action «%s»' % menu.action.name)

        menu_id = menu.id
        action_id = menu.action.id
        model = menu.action.res_model

        return WND_URL.format(
            action=action_id, model=model, view=view_type, menu=menu_id)

    @route(IMPUGNMENTS_URL, type='http', auth='user', website=False)
    def impugnments_url(self, **kw):
        menu_xid = 'academy_tests.menu_question_impugnment'

        base_url = self._base_url()
        relative_url = self._menu_to_url(menu_xid, view_type='kanban')
        full_url = urljoin(base_url, relative_url)

        return werkzeug.utils.redirect(full_url)
