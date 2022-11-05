# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingModuleTestCategoryRel(models.Model):
    """ This act as middle relation in many to many relationship between
    academy.tests.category and academy.training.module
    """

    _name = 'academy.training.module.test.category.rel'
    _description = u'Academy training module test category'

    _order = 'training_module_id DESC, test_category_id DESC'

    _auto = False

    test_category_id = fields.Many2one(
        string='Category',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related category',
        comodel_name='academy.tests.category',
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
         WITH linked AS (
            SELECT tree.requested_module_id,
                tree.responded_module_id,
                link.topic_id,
                link_rel.category_id
            FROM academy_training_module_rel tree
            JOIN academy_tests_topic_training_module_link link
                ON tree.responded_module_id = link.training_module_id
            LEFT JOIN
                academy_tests_category_tests_topic_training_module_link_rel
                AS link_rel
                ON link_rel.tests_topic_training_module_link_id = link.id
        ), direct_categories AS (
            SELECT linked.requested_module_id,
                linked.topic_id,
                linked.category_id
            FROM linked
            WHERE linked.category_id IS NOT NULL
        ), no_direct_categories AS (
            SELECT linked.requested_module_id,
                linked.topic_id,
                atc.id AS category_id
            FROM linked
            JOIN academy_tests_category atc ON atc.topic_id = linked.topic_id
            WHERE linked.category_id IS NULL
        ), full_set AS (
            SELECT direct_categories.requested_module_id,
                direct_categories.topic_id,
                direct_categories.category_id
            FROM direct_categories
            UNION ALL
            SELECT no_direct_categories.requested_module_id,
                no_direct_categories.topic_id,
                no_direct_categories.category_id
            FROM no_direct_categories
        )
        SELECT
            full_set.requested_module_id AS training_module_id,
            full_set.category_id AS test_category_id,
            full_set.topic_id
        FROM full_set
    '''
