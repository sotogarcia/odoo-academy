# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTestTopicRel(models.Model):
    """ This act as middle relation in many to many relationship between
    academy.tests.test and academy.tests.topic
    """

    _name = 'academy.tests.test.topic.rel'
    _description = u'Academy tests test topic'

    _order = 'test_id DESC, topic_id DESC'

    _auto = False

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related test',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related topic',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
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
        sentence = '''CREATE or REPLACE VIEW {} as ({})'''

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    # Raw sentence used to create new model based on SQL VIEW
    _view_sql = '''
        SELECT DISTINCT att.id AS test_id,
            atp.id AS topic_id
        FROM academy_tests_test att
        JOIN academy_tests_test_question_rel rel
            ON att.id = rel.test_id
        JOIN academy_tests_question atq
            ON atq.id = rel.question_id
        JOIN academy_tests_topic atp
            ON atq.topic_id = atp.id
        ORDER BY
            att.id, atp.id
    '''
