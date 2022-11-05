# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsQuestionTrainingModuleRel(models.Model):
    """ This act as middle relation in many to many relationship between
    academy.tests.question and academy.training.module
    """

    _name = 'academy.tests.question.training.module.rel'
    _description = u'Academy tests question training module'

    _order = 'question_id DESC, training_module_id DESC'

    _auto = False

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related question',
        comodel_name='academy.tests.question',
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
        WITH module_data AS (
            -- Topic, version and category by module (tree)
            SELECT
                requested_module_id AS training_module_id,
                link.topic_id,
                link.topic_version_id,
                rel.category_id
            FROM
                academy_tests_topic_training_module_link AS link
                INNER JOIN
                academy_tests_category_tests_topic_training_module_link_rel
                AS rel
                    ON rel.tests_topic_training_module_link_id = link."id"
                INNER JOIN academy_training_module_rel AS tree
                    ON responded_module_id = link.training_module_id
        ), question_data AS (
            -- Topic, version and category by question
            SELECT
                atq."id" AS question_id,
                atq.topic_id,
                rel1.topic_version_id,
                rel2.category_id
            FROM
                academy_tests_question AS atq
                INNER JOIN academy_tests_question_topic_version_rel AS rel1
                    ON rel1.question_id = atq."id"
                INNER JOIN academy_tests_question_category_rel AS rel2
                    ON atq."id" = rel2.question_id
        ), active_module_question_rel AS (
            -- Choose only matching active records
            SELECT
                training_module_id,
                question_id
            FROM
                module_data AS md
                -- Match module/question
                INNER JOIN question_data AS qd
                    ON md.topic_id = qd.topic_id
                        AND md.topic_version_id = qd.topic_version_id
                        AND md.category_id = qd.category_id
                -- Limit to active records in middle relations
                INNER JOIN academy_tests_topic AS att
                    ON att."id" = md.topic_id
                        AND att.active
                INNER JOIN academy_tests_topic_version AS ttv
                    ON ttv."id" = md.topic_version_id
                        AND ttv.active
                INNER JOIN academy_tests_category AS atc
                    ON atc."id" = md.category_id
                        AND atc.active
        )
        SELECT DISTINCT
            training_module_id,
            question_id
        FROM
            active_module_question_rel AS rel
    '''
