# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)


class AcademyTestsQuestionDependencyRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.tests.question.dependency.rel'
    _description = u'Academy tests question dependency rel'

    _auto = False
    _table = 'academy_tests_question_dependency_rel'
    _view_sql = '''
        WITH RECURSIVE questions AS (
            SELECT
                "id",
                depends_on_id,
                ARRAY[]::INT[] AS depends_on_ids,
                1::INT AS "sequence",
                ARRAY[1]::INT[] AS "sequences"
            FROM academy_tests_question
            WHERE "depends_on_id" IS NULL

            UNION ALL

            SELECT
                atq."id",
                atq."depends_on_id",
                array_append(
                    depends_on_ids, atq."depends_on_id") AS depends_on_ids,
                "sequence"+1 AS "sequence",
                array_append(sequences, "sequence" + 1)
            FROM  academy_tests_question AS atq
            INNER JOIN questions
                ON atq."depends_on_id" = questions."id"
        ),

        unpacked AS (
            SELECT
                "id" AS question_id,
                unnest(depends_on_ids) AS depends_on_id,
                        unnest(sequences) AS "sequence"
            FROM questions
        )
        SELECT DISTINCT
            unpacked.question_id,
            unpacked.depends_on_id
        FROM
            unpacked
        INNER JOIN academy_tests_question AS atq
            ON atq."id" = question_id
        WHERE
            unpacked."depends_on_id" IS NOT NULL
    '''

    question_id = fields.Many2one(
        string='Question',
        required=False,
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

    depends_on_id = fields.Many2one(
        string='Depends on',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Question which depends on',
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
