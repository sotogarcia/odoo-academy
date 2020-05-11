# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.answers.table. an unique Odoo model
which contains all academy tests attributes and behavior.

This model uses an SQL view instead an SQL table, therefore it do not store
any data. Each one of the records for this model will represent an entry in
the answers table for a tests, this table is usually attached to the related
test.

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import drop_view_if_exists


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestsAnswersTable(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

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
        # oldname='academy_test_id'
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
        # oldname='academy_question_id'
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

    @api.depends('question_id')
    def _compute_category_ids(self):
        for record in self:
            ids = record.question_id.category_ids.mapped('id') or []
            record.category_ids = [(6, None, ids)]


    # @api.model_cr
    def init(self):
        """ Build database view which will be used as module origin

            :param cr: database cursor
        """

        _sql_query = u"""
            WITH ordered_answers AS (
                -- Ensure answers sequence
                SELECT
                    academy_tests_answer."id",
                    (
                        ROW_NUMBER () OVER (
                            PARTITION BY academy_tests_answer.question_id
                            ORDER BY
                                academy_tests_answer.question_id ASC,
                                academy_tests_answer."sequence" ASC,
                                academy_tests_answer."id" ASC
                        )
                    ) :: INTEGER AS "sequence",
                    academy_tests_answer.question_id,
                    academy_tests_answer.is_correct
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
                    ROW_NUMBER () OVER (
                        PARTITION BY rel.test_id
                        ORDER BY
                            rel.test_id DESC,
                            rel."sequence" ASC,
                            rel.question_id ASC
                    ) AS atq_index
                FROM
                    academy_tests_test_question_rel AS rel
                WHERE
                    active = TRUE
                ORDER BY
                    rel.test_id DESC,
                    rel."sequence" ASC,
                    rel.question_id ASC
            ) -- Main query
            SELECT
                ROW_NUMBER () OVER (

                    ORDER BY
                        oq.test_id DESC,
                        oq.atq_index ASC,
                        oq.question_id ASC,
                        oa."sequence" ASC,
                        oa."id" ASC
                ) :: INTEGER AS "id",
                oq.test_id :: INTEGER,
                oq.question_id :: INTEGER,
                oa."id" :: INTEGER AS academy_tests_answer_id,
                oq.atq_index :: INTEGER AS "sequence",
                SUBSTRING (
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                    FROM
                        oa."sequence" FOR 1
                ) :: VARCHAR AS "name",
                atq."description" :: TEXT
            FROM
                ordered_quesions AS oq
            LEFT JOIN (
                SELECT
                    *
                FROM
                    ordered_answers
                WHERE
                    is_correct IS TRUE
            ) AS oa ON oq.question_id = oa.question_id
            LEFT JOIN academy_tests_question AS atq ON atq."id" = oq.question_id
            ORDER BY
                oq.test_id DESC,
                oq.atq_index ASC,
                oq.question_id ASC,
                oa."sequence" ASC,
                oa."id" ASC
        """

        drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            'create or replace view {} as ({})'.format(
                self._table,
                _sql_query
            )
        )
