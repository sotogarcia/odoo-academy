# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.addons.website.models import ir_ui_view
from openerp import models, fields, api, tools
from openerp.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class IrUiView(ir_ui_view.View):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _inherit = ['ir.ui.view']


    def _get_module_by_id(self, xml_id):
        module = False

        try:
            view_domain = ['&', ('res_id', '=', xml_id), ('model', '=', 'ir.ui.view')]
            view_obj = self.env['ir.ui.view']
            view_set = view_obj.search(view_domain, limit=1)
            module = view_set.module
        except: # pylint: disable=locally-disabled, W0702
            pass

        return module


    @staticmethod
    def _get_module_by_xmlid(xml_id):
        module = False

        try:
            module = xml_id.split('.')[0]
        except: # pylint: disable=locally-disabled, W0702
            pass

        return module


    def _is_test_module(self, xml_id, modules):
        _logger.debug('Overwritten get_view_id (xml_id: %s', xml_id)

        if isinstance(xml_id, int):
            module = self._get_module_by_id(xml_id)
        else:
            module = self._get_module_by_xmlid(xml_id)

        return module in modules


    @api.model
    @tools.ormcache_context('self._uid', 'xml_id', keys=('website_id',))
    def get_view_id(self, xml_id):
        """ When website module is installed, website_id attribute
        stored in context disable report access by url, but this module
        needs to have this access active for some views.
        This overloaded method check if view xml_id is in list then
        removes website_id from context.
        NOTE: This is only a temporal patch, it will be changed by
        another solution.
        """

        modules = ['academy_tests', 'academy_tests_web']
        ctx = self.env.context

        if self._is_test_module(xml_id, modules) and 'website_id' in ctx:
            ctx = {item:ctx[item] for item in ctx if item != 'website_id'}

        return super(IrUiView, self.with_context(ctx)).get_view_id(xml_id)







