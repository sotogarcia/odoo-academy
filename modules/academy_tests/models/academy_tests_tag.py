# -*- coding: utf-8 -*-
""" AcademyTestsTag

This module contains the academy.tests.tag Odoo model which stores
all academy tests tag attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTag(models.Model):
    """ This is a property of the academy.tests.test model
    """

    _name = 'academy.tests.tag'
    _description = u'Academy tests, question tag'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = [
        'ownership.mixin'
    ]

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_name(),
        help='Name for this tag',
        size=255,
        translate=True
    )

    def default_name(self):
        name = ''

        uid = self.env.context.get('uid', False)
        if uid:
            user = self.env['res.users'].browse(uid)
            name = ' '.join(user.name.split(' ', 2)[:2])
            if name:
                name = name + ': '

        return name

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this question',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it')
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Questions relating to this tag',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_tag_rel',
        column1='tag_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
    )

    question_count = fields.Integer(
        string='Question count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute='_compute_question_count',
        search='_search_question_count',
    )

    @api.depends('question_ids')
    def _compute_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)

    test_ids = fields.Many2many(
        string='Tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Tests relating to this tag',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_tag_rel',
        column1='tag_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
    )

    test_count = fields.Integer(
        string='Test count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute='_compute_test_count'
    )

    @api.depends('test_ids')
    def _compute_test_count(self):
        for record in self:
            record.test_count = len(record.test_ids)

    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'tag_uniq',
            'UNIQUE(name)',
            _(u'There is already another tag with the same name')
        )
    ]
