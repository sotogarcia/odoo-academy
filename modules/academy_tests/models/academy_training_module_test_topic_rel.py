# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists

_logger = getLogger(__name__)


class AcademyTrainingModuleTestTopicRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.training.module.test.topic.rel'
    _description = 'Academy training module test topic rel'

    _auto = False
    _table = 'academy_training_module_test_topic_rel'
    _view_sql = '''
        SELECT
            tree."requested_module_id" as training_module_id,
            link."topic_id" as test_topic_id
        FROM
            academy_training_module_tree_readonly AS tree
        INNER JOIN academy_tests_topic_training_module_link AS link
            ON tree."responded_module_id" = link."training_module_id"
    '''

    test_topic_id = fields.Many2one(
        string='Test topic',
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

    training_module_id = fields.Many2one(
        string='Training module',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related training module',
        comodel_name='academy.training.module',
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
