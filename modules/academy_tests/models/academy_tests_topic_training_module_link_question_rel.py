# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTopicTrainingModuleLinkQuestionRel(models.Model):
    """ This act as middle relation in many to many relationship
    """

    _name = 'academy.tests.topic.training.module.link.question.rel'
    _description = u'Relationship between training modules and test topics'

    _order = 'topic_module_link_id DESC,  question_id DESC'

    _auto = False

    topic_module_link_id = fields.Many2one(
        string='Link',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related training module-test topic link',
        comodel_name='academy.tests.topic.training.module.link',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related test question',
        comodel_name='academy.tests.question',
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
    # Computes all question dependencies based on chosen topics and categories
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
