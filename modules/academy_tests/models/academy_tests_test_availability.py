# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)



SQL_FOR_ACADEMY_TESTS_TEST_AVAILABILITY = '''
WITH all_data AS (
    SELECT
        test_id,
        'academy.training.module' :: VARCHAR AS model,
        training_module_id AS res_id
    FROM
        academy_tests_test_training_module_rel UNION
    SELECT
        test_id,
        'academy.competency.unit' :: VARCHAR AS model,
        competency_unit_id AS res_id
    FROM
        academy_tests_test_competency_unit_rel UNION
    SELECT
        test_id,
        'academy.training.activity' :: VARCHAR AS model,
        training_activity_id AS res_id
    FROM
        academy_tests_test_training_activity_rel UNION
    SELECT
        test_id,
        'academy.training.action' :: VARCHAR AS model,
        training_action_id AS res_id
    FROM
        academy_tests_test_training_action_rel UNION
    SELECT
        test_id,
        'academy.training.action.enrolment' :: VARCHAR AS model,
        enrolment_id AS res_id
    FROM
        academy_tests_test_training_action_enrolment_rel
)
SELECT
    ROW_NUMBER() OVER()::INTEGER AS "id",
    1::INTEGER AS create_uid,
    1::INTEGER AS write_uid,
    CURRENT_TIMESTAMP AS create_date,
    CURRENT_TIMESTAMP AS write_date,
    test_id,
    model,
    res_id,
    (model || ',' || res_id)::VARCHAR AS related_id
    FROM all_data
'''



class AcademyTestsTestAvailability(models.Model):
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

    _table='academy_tests_test_availability'


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
        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute('''CREATE or REPLACE VIEW {} as (
            {}
        )'''.format(
            self._table,
            SQL_FOR_ACADEMY_TESTS_TEST_AVAILABILITY)
        )

        self.prevent_actions()
