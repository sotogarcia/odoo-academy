# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import http
from odoo.http import request, Response
from odoo.http import content_disposition
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


NEW_TEST = '/academy_tests_templates/new_test/<int:code>'


class TemplatesAPI(http.Controller):
    """ Allows to call templates from external apps
    """

    @http.route(NEW_TEST, type='http', auth='user')
    def new_test(self, code):

        pass
