# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, api
from logging import getLogger

_logger = getLogger(__name__)


class IrRule(models.Model):
    """ Bypass ir.rule to get schedule with all companies
    """

    _name = 'ir.rule'
    _inherit = 'ir.rule'

    @api.model
    def domain_get(self, model_name, mode='read'):

        if self.env.context.get('academy_timesheet_for_all_companies', False):
            company_ids = self.get_user_company_ids()
            if company_ids:
                context = self.env.context.copy()
                context.update(allowed_company_ids=company_ids)
                self = self.with_context(context)

        parent = super(IrRule, self)
        result = parent.domain_get(model_name=model_name, mode=mode)

        return result

    @api.model
    def get_user_company_ids(self):
        user = self.env.user
        return user.company_ids.ids
