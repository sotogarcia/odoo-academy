# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists
from . import academy_tests_question_training_activity_rel as activity_rel


_logger = getLogger(__name__)


class AcademyTestsQuestionTrainingModuleRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.tests.question.training.module.rel'
    _description = u'Academy tests question training module rel'

    _auto = False
    _table = 'academy_tests_question_training_module_rel'
    _view_sql = '''
    {}
    SELECT DISTINCT
        training_module_id,
        question_id
    FROM
        active_module_question_rel AS rel
    '''

    question_id = fields.Many2one(
        string='Question',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Original question',
        comodel_name='academy.tests.question',
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

        view_sql = self._view_sql.format(
            activity_rel.PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE)
        self.env.cr.execute(sentence.format(self._table, view_sql))

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
