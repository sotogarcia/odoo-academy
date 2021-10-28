# -*- coding: utf-8 -*-
""" AcademyTestsAnswersTable

This module contains the academy.tests.answer.table Odoo model which stores
all academy tests answer table attributes and behavior.
"""

from logging import getLogger

from odoo import models, fields, api
from odoo.tools import drop_view_if_exists

from .utils.view_academy_tests_answers_table import \
    ACADEMY_TESTS_ANSWERS_TABLE_MODEL

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

    def init(self):
        """ Build database view which will be used as module origin

            :param cr: database cursor
        """

        drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            'create or replace view {} as ({})'.format(
                self._table,
                ACADEMY_TESTS_ANSWERS_TABLE_MODEL
            )
        )
