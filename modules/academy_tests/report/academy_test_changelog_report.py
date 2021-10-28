# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestChangelogReport(models.AbstractModel):
    """ academy.test.changelog.report custom report
    """

    _name = 'report.academy_tests.view_academy_tests_test_changelog_qweb'

    _description = 'Report to build a test question changelog'

    _report_xid = 'academy_tests.action_report_test_changelog'
    _target_model = 'academy.tests.test'

    def translate(self, string):
        return _(string)

    def is_correct(self, value):
        return _('Yes') if value else _('No')

    @api.model
    def _get_report_values(self, docids, data=None):

        # report_obj = self.env['ir.actions.report']
        # report = report_obj._get_report_from_name(self._report_xid)

        test_domain = [('id', 'in', docids)]
        test_obj = self.env[self._target_model]
        test_set = test_obj.search(test_domain)

        docargs = {
            'doc_ids': docids,
            'doc_model': self.env['academy.tests.test'],
            'data': data,
            'docs': test_set,
            'report': self
        }

        return docargs
