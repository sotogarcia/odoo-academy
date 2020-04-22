# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestReport(models.AbstractModel):
    """ This model has been created only to be extended by another modules
    """

    _name = 'report.academy_tests.view_academy_tests_qweb'

    _description = 'Report to print tests'

    _report_xid = 'academy_tests.action_report_printable_test'
    _target_model = 'academy.tests.test'


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
        }

        return docargs
