# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTestBlock(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.test.block'
    _description = u'This act as label to allow grouping test questions'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=50,
        translate=True
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

    preamble = fields.Text(
        string='Preamble',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new preamble',
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

    link_ids = fields.Many2many(
        string='Question links',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.test.question.rel',
        relation='academy_tests_test_block_link_rel',
        column1='block_id',
        column2='link_id',
        domain=[],
        context={},
        limit=None
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        relation='academy_tests_test_block_question_rel',
        column1='block_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_question_ids'
    )

    test_ids = fields.Many2many(
        string='Tests',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        relation='academy_tests_test_block_test_rel',
        column1='block_id',
        column2='tests_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_tests_ids'
    )

    @api.depends('link_ids')
    def _compute_question_ids(self):
        for record in self:
            ids = record.mapped('link_ids.question_id.id')
            record.question_ids = [(6, 0, ids)]

    @api.depends('link_ids')
    def _compute_tests_ids(self):
        for record in self:
            ids = record.mapped('link_ids.test_id.id')
            record.test_ids = [(6, 0, ids)]
