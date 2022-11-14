# -*- coding: utf-8 -*-
""" AcademyTestsQuestionType

This module contains the academy.tests.question.type Odoo model which stores
all academy tests question type attributes and behavior.
"""

from odoo import models, fields, api

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsQuestionType(models.Model):
    """ This is a property of the academy.tests.question model
    """

    _name = 'academy.tests.question.type'
    _description = u'Academy tests, question type'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
        translate=True,
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    question_ids = fields.One2many(
        string='Question',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Show the list of questions related to this version',
        comodel_name='academy.tests.question',
        inverse_name='type_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    question_count = fields.Integer(
        string='Question count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of questions related to this category',
        compute='_compute_question_count',
        search='_search_question_count'
    )

    @api.depends('question_ids')
    def _compute_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)
