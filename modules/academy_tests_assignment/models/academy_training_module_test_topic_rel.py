# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingModuleTestTopicRel(models.Model):
    """ This act as middle relation in many to many relationship between
    academy.training.module and academy.tests.topic
    """

    _name = 'academy.training.module.test.topic.rel'
    _description = u'Academy training module test topic'

    _order = 'training_module_id DESC, test_topic_id DESC'

    _auto = False

    test_topic_id = fields.Many2one(
        string='test_topic_id',
        required=True,
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
        required=True,
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
        SELECT
            tree.requested_module_id AS training_module_id,
            link.topic_id AS test_topic_id
        FROM
            academy_training_module_rel tree
        JOIN academy_tests_topic_training_module_link link
            ON tree.responded_module_id = link.training_module_id
    '''
