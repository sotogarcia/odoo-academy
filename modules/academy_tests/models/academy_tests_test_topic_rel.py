# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)


class AcademyTestsTestTopicRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.tests.test.topic.rel'
    _description = u'Academy tests test topic rel'

    _auto = False
    _table = 'academy_tests_test_topic_rel'
    _view_sql = '''
    SELECT DISTINCT
        att."id" AS test_id,
        atp."id" AS topic_id
    FROM
        academy_tests_test AS att
    INNER JOIN academy_tests_test_question_rel AS rel
        ON att."id" = rel.test_id
    INNER JOIN academy_tests_question AS atq
        ON atq."id" = rel.question_id
    INNER JOIN academy_tests_topic AS atp
        ON atq.topic_id = atp."id"
    ORDER BY
        att."id" ASC,
        atp."id" ASC
    '''

    test_id = fields.Many2one(
        string='Test',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related tests',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related test topic',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def init(self):
        sentence = 'CREATE or REPLACE VIEW {} as ( {} )'

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)
