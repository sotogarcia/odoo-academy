# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)


class AcademyTestsQuestionDuplicatedByOwnerRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.tests.question.duplicated.by.owner.rel'
    _description = 'Academy tests question duplicated by owner rel'

    _auto = False
    _table = 'academy_res_users_duplicated_questions_rel'  # Different name
    _view_sql = '''
    WITH duplicates AS (
        SELECT
            checksum,
            MIN ( atq."id" ) :: INTEGER AS original_id,
            ARRAY_AGG ( atq."id" ) :: INTEGER [] AS question_ids
        FROM
            academy_tests_question AS atq
        WHERE
            checksum IS NOT NULL
            AND status <> 'draft'
            AND active = True
        GROUP BY
            checksum
        HAVING
            COUNT ( atq."id" ) > 1
    ), unnested AS (
        SELECT
            original_id AS question_id,
            UNNEST ( question_ids ) AS duplicate_id
        FROM
            duplicates
    )
    SELECT
        duplicate_id,
        "duplicate_atq"."owner_id" AS duplicate_owner_id
    FROM
        unnested AS unn
        INNER JOIN academy_tests_question AS duplicate_atq
            ON duplicate_atq."id" = duplicate_id
    WHERE
        question_id <> duplicate_id
    ORDER BY
        question_id ASC,
        duplicate_id DESC
    '''

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

    duplicate_owner_id = fields.Many2one(
        string='Owner',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Question owner',
        comodel_name='res.users',
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
