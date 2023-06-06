# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsUncategorizedByUserReadonly(models.Model):
    """ Count uncategorized questions by user and topic
    """

    _name = 'academy.tests.uncategorized.by.user.readonly'
    _description = u'Academy tests uncategorized by user'

    _rec_name = 'owner_id'
    _order = 'owner_id ASC'

    _inherit = []

    owner_id = fields.Many2one(
        string='Owner',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Current owner',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show the topic of the questions',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_count = fields.Integer(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of uncategorized questions'
    )

    _auto = False
    _table = 'academy_tests_uncategorized_by_user_readonly'
    _view_sql = '''
        WITH raw_data AS (
            SELECT DISTINCT ON ( atq."id" )
                atq.owner_id,
                atq.topic_id,
                atq."id" AS question_id
            FROM
                academy_tests_question AS atq
                LEFT JOIN academy_tests_topic AS atp
                    ON atp."id" = atq.topic_id
                LEFT JOIN academy_tests_question_category_rel AS rel1
                    ON rel1.question_id = atq."id"
                LEFT JOIN academy_tests_category AS atc
                    ON atc."id" = rel1.category_id
                LEFT JOIN academy_tests_question_topic_version_rel AS rel2
                    ON rel2.question_id = atq."id"
                LEFT JOIN academy_tests_topic_version AS attv
                    ON rel2.topic_version_id = attv."id"
            WHERE
                atq.active AND (
                    atp."id" IS NULL
                    OR atc."id" IS NULL
                    OR attv."id" IS NULL
                    OR atp."active" IS FALSE
                    OR atc."active" IS FALSE
                    OR attv."active" IS FALSE
                    OR atp."provisional" IS TRUE
                    OR atc."provisional" IS TRUE
                    OR attv."provisional" IS TRUE
                )
        )
        SELECT
            ROW_NUMBER() OVER()::INTEGER AS "id",
            owner_id,
            topic_id,
            COUNT ( question_id ) :: INTEGER AS question_count
        FROM
            raw_data
        GROUP BY
            owner_id,
            topic_id
        ORDER BY
            owner_id,
            topic_id
    '''

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
