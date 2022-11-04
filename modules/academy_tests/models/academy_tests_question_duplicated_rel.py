# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsQuestionDuplicatedRel(models.Model):
    """ This act as middle relation in many to many relationship
    """

    _name = 'academy.tests.question.duplicated.rel'
    _description = u'List all duplicated questions'

    _order = 'question_id DESC,  duplicate_id DESC'

    _auto = False

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Target question',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    duplicate_id = fields.Many2one(
        string='Depends on',
        required=True,
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
            question_id,
            duplicate_id
        FROM
            unnested AS unn
        WHERE
            question_id <> duplicate_id
        ORDER BY
            question_id ASC,
            duplicate_id DESC
    '''
