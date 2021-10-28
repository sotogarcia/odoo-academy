# -*- coding: utf-8 -*-
""" AcademyTestsTestAvailabilityReadonly

This module contains the academy.tests.test.availability Odoo model which
builds a SQL VIEW based model to quick search relationship between tests and
other models like: training modules or units,  competency units, training
activities, training actions and training action enrolments
"""

from odoo import models, fields

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_test_availability import \
    ACADEMY_TESTS_TEST_AVAILABILITY_MODEL

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTestAvailabilityReadonly(models.Model):
    """ Lists the records of all the models to which this test has been
    linked. An Odoo `fields.Reference` field type has been use to show
    linked records.

    Model uses a SQL view instead a regular table, it fetches records
    from several tables to list them together.
    """

    _name = 'academy.tests.test.availability'
    _description = u'Academy tests test availability'

    _rec_name = 'id'
    _order = 'id ASC'

    _auto = False

    _table = 'academy_tests_test_availability_readonly'
    _sql_query = ACADEMY_TESTS_TEST_AVAILABILITY_MODEL

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Choose test will be available in',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    model = fields.Selection(
        string='Model',
        required=False,
        readonly=True,
        index=False,
        default=False,
        help='Choose related record model',
        selection=[
            ('academy.training.module', 'Training module/unit'),
            ('academy.competency.unit', 'Competency unit'),
            ('academy.training.activity', 'Training activity'),
            ('academy.training.action', 'Training action'),
            ('academy.training.action.enrolment', 'Enrolment')
        ]
    )

    res_id = fields.Integer(
        string='Resource ID',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Choose related record ID'
    )

    related_id = fields.Reference(
        string='Related',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Choose record to which test has been linked',
        selection=[
            ('academy.training.module', 'Training module/unit'),
            ('academy.competency.unit', 'Competency unit'),
            ('academy.training.activity', 'Training activity'),
            ('academy.training.action', 'Training action'),
            ('academy.training.action.enrolment', 'Enrolment')
        ]
    )

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)

    def init(self):
        sentence = 'CREATE or REPLACE VIEW {} as ( {} )'

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._sql_query))

        self.prevent_actions()
