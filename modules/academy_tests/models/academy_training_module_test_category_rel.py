# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)


class AcademyTrainingModuleTestCategoryRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.training.module.test.category.rel'
    _description = 'Academy training module test category rel'

    _auto = False
    _table = 'academy_training_module_test_category_rel'
    _view_sql = '''
    WITH linked AS (
        SELECT
            tree."requested_module_id",
            tree."responded_module_id",
            link."topic_id",
            link_rel."category_id"
        FROM
            academy_training_module_tree_readonly AS tree
        INNER JOIN academy_tests_topic_training_module_link AS link
            ON tree."responded_module_id" = link."training_module_id"
        LEFT JOIN academy_tests_category_tests_topic_training_module_link_rel
            AS link_rel
            ON link_rel."tests_topic_training_module_link_id" = link."id"
    ), direct_categories AS (
        SELECT
            requested_module_id,
            topic_id,
            category_id
        FROM
            linked
        WHERE
            category_id IS NOT NULL
    ), no_direct_categories AS (
        SELECT
            requested_module_id,
            linked."topic_id",
            atc."id" AS category_id
        FROM
            linked
        INNER JOIN academy_tests_category AS atc
            ON atc."topic_id" = linked."topic_id"
        WHERE
            linked."category_id" IS NULL
    ), full_set as (
        SELECT
            *
        FROM
            direct_categories
        UNION ALL SELECT
            *
        FROM
            no_direct_categories
    ) SELECT
        requested_module_id AS training_module_id,
        category_id AS test_category_id,
        topic_id
    FROM full_set
    '''

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

    test_category_id = fields.Many2one(
        string='Test category',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related test category',
        comodel_name='academy.tests.category',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_id = fields.Many2one(
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
