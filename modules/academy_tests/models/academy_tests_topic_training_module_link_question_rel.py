# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)


class AcademyTestsTopicTrainingModuleLinkQuestionRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.tests.topic.training.module.link.question.rel'
    _description = u'Academy tests topic training module link question rel'

    _auto = False
    _table = 'academy_tests_topic_training_module_link_question_rel'
    _view_sql = '''
        WITH questions AS (

            -- List all questions with their topic, version and categories
            SELECT
                atq."id" AS question_id,
                atq.topic_id,
                vrel.topic_version_id AS version_id,
                crel.category_id
            FROM
                academy_tests_question AS atq
            INNER JOIN academy_tests_question_category_rel AS crel
                ON crel.question_id = atq."id"
            INNER JOIN academy_tests_question_topic_version_rel AS vrel
                ON vrel.question_id = atq."id"

        ), topic_module_links AS (

            -- List all links with their topic, version and categories
            SELECT
                link."id" AS topic_module_link_id,
                topic_id,
                topic_version_id AS version_id,
                rel.category_id
            FROM academy_tests_topic_training_module_link AS link
            JOIN academy_tests_category_tests_topic_training_module_link_rel
                AS rel
                ON rel.tests_topic_training_module_link_id = link."id"

        )

        -- INNER JOIN when matching topic, version and categories
        SELECT DISTINCT
            topic_module_link_id,
            question_id
        FROM
            questions AS atq
        INNER JOIN topic_module_links AS tml
            ON tml.topic_id = atq.topic_id
            AND tml.version_id = atq.version_id
            AND tml.category_id = atq.category_id
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

    duplicate_id = fields.Many2one(
        string='Duplicated',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Duplicated question',
        comodel_name='academy.tests.question',
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
