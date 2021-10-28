# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Test Report Townhall

This module contains the academy.test.report.townhall an unique Odoo model
which contains all Academy Test Report Townhall attributes and behavior.

Todo:
    - [x] Add report class
    - [x] Move code to the report class
    - [x] Add pagebreak before answer table
    * Rename o

"""


from logging import getLogger
from re import search

# pylint: disable=locally-disabled, E0401
from openerp import models, api
from openerp.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestReportTownhall(models.AbstractModel):
    """ This controls the academy test report townhall.

    Public methods
    - townhall_file: this uses regex to search for filename in question
    preamble, this is needed to fill tawnhall test template.
    """


    _name = 'report.academy_tests_reports.view_academy_test_townhall_qweb'
    _description = u'Academy tests, report for townhall'

    _model = 'academy.tests.test'



    @api.model
    def get_report_values(self, docids, data=None):
        """ This adds a self reference as named ``report `` item, then public
        methods in this object can be called from report.
        """

        test_domain = [('id', 'in', docids)]
        test_obj = self.env[self._model]
        test_set = test_obj.search(test_domain)

        return {
            'doc_ids': docids,
            'doc_model': self._model,
            'docs': test_set,
            'data': data,
            'report': self
        }



    @api.model
    # pylint: disable=locally-disabled, R0201
    def townhall_file(self, preamble):
        """ This searches for file name in given question preamble and return
        it as an string

        @param (string): question preamble
        @return returns filename or empty string
        """

        matches = search(r'[a-zA-Z0-9-_]+\.[A-Za-z]{1,3}(?!\w)', preamble)

        return matches.group() if matches else ''

