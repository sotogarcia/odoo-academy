# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger
from enum import IntEnum

_logger = getLogger(__name__)

class AcademyTestsUncategorizedByUserReport(models.AbstractModel):
    """ Get data to be used in report
    """

    _name = ('report.academy_tests.view_uncategorized_by_user_report_qweb')

    _description = 'Uncategorized questions by user'

    _report_xid = ('academy_tests.action_report_uncategorized_by_user')

    _target_model = 'res.users'

    @api.model
    def _search_owners(self, ids):
        user_domain = [('id', 'in', ids)]
        user_set = self.env['res.users']

        return user_set.search(user_domain)

    @api.model
    def _get_report_values(self, docids, data=None):
        owner_set = self._search_owners(docids)

        return {
            'doc_ids': docids,
            'doc_model': self.env['res.users'],
            'data': data,
            'docs': owner_set,
            'report': self
        }
