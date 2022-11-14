# -*- coding: utf-8 -*-
""" AcademyTestsLevel

This module contains the academy.tests.level Odoo model which stores
all academy tests level attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsLevel(models.Model):
    """ This is a property of the academy.tests.test model
    """

    _name = 'academy.tests.level'
    _description = u'Academy tests, question difficulty level'

    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this level',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this level',
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

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help='Sequence order for difficulty'
    )

    question_ids = fields.One2many(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List the related questions',
        comodel_name='academy.tests.question',
        inverse_name='level_id',
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
        help=False,
        compute='_compute_question_count',
        search='_search_question_count',
    )

    @api.depends('question_ids')
    def _compute_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)

    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'level_uniq',
            'UNIQUE(name)',
            _(u'There is already another level with the same name')
        )
    ]
