# -*- coding: utf-8 -*-
""" AcademyTestsAnswersTable

This module contains the academy.tests.answer.table Odoo model which stores
all academy tests answer table attributes and behavior.
"""

from logging import getLogger

from odoo import models, fields, api
from odoo.tools import drop_view_if_exists

_logger = getLogger(__name__)


class AcademyTestsAnswersTable(models.Model):
    """ This model uses an SQL VIEW to create an answer table for a test
    """

    _name = 'academy.tests.answers.table'
    _description = u'Academy tests, answers table entry'

    _rec_name = 'name'
    _order = 'sequence ASC, id ASC'

    _auto = False

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Letter for this answer',
        size=1024,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this question',
        translate=True
    )

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Test to which this item belongs',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question to which this answer belongs',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    link_id = fields.Many2one(
        string='Test/Question link',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Test question relationship',
        comodel_name='academy.tests.test.question.rel',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help='Preference order for this question'
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute=lambda self: self._compute_topic_id()
    )

    @api.depends('question_id')
    def _compute_topic_id(self):
        for record in self:
            record.topic_id = record.question_id.topic_id

    category_ids = fields.Many2many(
        string='Categories',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.category',
        relation='academy_test_answer_table_category_rel',
        column1='answer_table_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None,
        compute=lambda self: self._compute_category_ids()
    )

    block_id = fields.Many2one(
        string='Block',
        related='link_id.block_id'
    )

    @api.depends('question_id')
    def _compute_category_ids(self):
        for record in self:
            ids = record.question_id.category_ids.mapped('id') or []
            record.category_ids = [(6, None, ids)]

    def init(self):
        """ Build database view which will be used as module origin

            :param cr: database cursor
        """

        drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            'create or replace view {} as ({})'.format(
                self._table,
                self._sql
            )
        )

    _sql = '''
        -- MODEL: academy_tests.model_academy_tests_answers_table
        -- Thiswill be used to build and display as report a test answers table

        -- ┌───────────────────┐
        -- │ _answers_table    │
        -- ├───────────────────┤
        -- │ id                │   - Virtual ID. This should not be used
        -- │ question_id       │
        -- │ sequence          │   - Partitioned by test, ordered by sequence
        -- │ name              │
        -- │ description       │
        -- │ link_id           │
        -- └───────────────────┘

        WITH ordered_answers AS (
            -- Ensure answers sequence

            SELECT
                academy_tests_answer."id",
                ROW_NUMBER ( ) OVER (
                    PARTITION BY academy_tests_answer.question_id
                    ORDER BY academy_tests_answer.question_id ASC,
                             academy_tests_answer."sequence" ASC,
                             academy_tests_answer."id" ASC
                ) :: INTEGER AS "sequence",
                academy_tests_answer.question_id,
                academy_tests_answer.is_correct,
                SUBSTRING (
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' :: VARCHAR,
                    ROW_NUMBER ( ) OVER (
                        PARTITION BY academy_tests_answer.question_id
                        ORDER BY academy_tests_answer.question_id ASC,
                        academy_tests_answer."sequence" ASC,
                        academy_tests_answer."id" ASC
                    ) :: INTEGER, 1 ) :: VARCHAR AS "name"
            FROM
                academy_tests_answer
            WHERE
                active = TRUE
            ORDER BY
                academy_tests_answer.question_id ASC,
                academy_tests_answer."sequence" ASC,
                academy_tests_answer."id" ASC

        ),

        ordered_quesions AS (
            -- Ensure questions sequence

            SELECT
                rel.test_id,
                rel.question_id,
                ROW_NUMBER ( ) OVER (
                    PARTITION BY rel.test_id
                    ORDER BY rel.test_id DESC, rel."sequence" ASC, rel."id" ASC
                ) AS atq_index
            FROM
                academy_tests_test_question_rel AS rel
            ORDER BY
                rel.test_id DESC,
                rel."sequence" ASC,
                rel."id" ASC

        ),

        main_query AS (
            -- Main query

            SELECT
                oq.test_id :: INTEGER,
                oq.question_id :: INTEGER,
                STRING_AGG(
                    oa."name",
                    ', '
                    ORDER BY oa."name" ASC
                ) :: VARCHAR "name",
                MIN ( atq_index ) :: INTEGER AS atq_index
            FROM
                ordered_quesions AS oq
            LEFT JOIN (
                    SELECT
                        *
                    FROM
                        ordered_answers
                    WHERE is_correct IS TRUE
                ) AS oa
                ON oq.question_id = oa.question_id
            GROUP BY
                oq.test_id,
                oq.question_id

        )

        SELECT
            ROW_NUMBER ( ) OVER (
                ORDER BY mq.test_id DESC, atq_index ASC
            ) :: INTEGER AS "id",
            mq.test_id,
            mq.question_id,
            ROW_NUMBER ( ) OVER (
                PARTITION BY mq.test_id
                ORDER BY mq.test_id DESC, atq_index ASC
            ) :: INTEGER AS "sequence",
            mq."name",
            description,
                rel."id" AS link_id
        FROM
            main_query AS mq
        INNER JOIN academy_tests_question AS atq
            ON atq."id" = mq."question_id"
        INNER JOIN academy_tests_test_question_rel AS rel
            ON rel.test_id = mq.test_id AND rel.question_id = mq.question_id
    '''
