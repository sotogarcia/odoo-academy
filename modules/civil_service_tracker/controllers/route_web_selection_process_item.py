# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from openerp.http import route, request
from .base_controller import BasePublicController
from odoo.tools.misc import format_date as fmt_date
from openerp.tools.translate import _

from logging import getLogger


ROUTE = '/civil-service-tracker/web/selection-process/item/<string:token>'
TEMPLATE = 'civil_service_tracker.route_web_selection_process_item'

_logger = getLogger(__name__)


class WebsSelectionProcessItem(BasePublicController):

    @route(ROUTE, type='http', auth='user', website=True, csrf=True,
           methods=['GET'])
    def web_selection_proccess_item(self, token=None, **kwargs):
        
        # if not request.session.uid:
        #     # Establecer el usuario público si no hay sesión activa
        #     request.uid = request.env.ref('base.public_user').id

        process_obj = request.env['civil.service.tracker.selection.process']
        process_obj = process_obj.sudo()

        domain = self._make_token_domain(token)

        process = process_obj.search(domain)
        if not process or len(process) > 1:
            _logger.error(f'No process was found for the given token: {token}')
            return request.not_found()

        name = process.name
        _logger.debug(f'The process {name} matches the provided token {token}')

        values = {
            'process': process, 
            'page_title': name,
            'format_date': lambda dt: fmt_date(
                request.env, dt, date_format=False
            ),
            'remove_scheme': self.remove_scheme,
            'abs_url': self.secure_absolute_url
        }

        return request.render(TEMPLATE, values)
