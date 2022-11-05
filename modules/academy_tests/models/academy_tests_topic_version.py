# -*- coding: utf-8 -*-
""" AcademyTestsTopicVersion

This module contains the academy.tests.topic.version Odoo model which stores
all academy tests topic version attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN
from odoo.exceptions import UserError

from .utils.libuseful import fix_established, is_numeric
from .utils.sql_inverse_searches import VERSION_QUESTION_COUNT_SEARCH
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTopicVersion(models.Model):
    """ A topic can have more than one versions, this model represents these
    versions.
    """

    _name = 'academy.tests.topic.version'
    _description = u'Academy tests topic version'

    _rec_name = 'name'
    _order = 'sequence DESC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this version',
        size=1024,
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this version or uncheck to archivate'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this version',
        translate=True
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help=('Place of this version in the order of the versions from parent')
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the parent topic',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    provisional = fields.Boolean(
        string='Provisional',
        required=False,
        readonly=False,
        index=True,
        default=False,
        help='Check it to indicate the version is not definitive'
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Show the list os questions related to this topic version',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_topic_version_rel',
        column1='topic_version_id',
        column2='question_id',
        domain=[],
        context={},
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

    def _search_question_count(self, operator, operand):
        supported = ['=', '!=', '<=', '<', '>', '>=']

        assert operator in supported, \
            UserError(_('Search operator not supported'))

        assert is_numeric(operand) or operand in [True, False], \
            UserError(_('Search value not supported'))

        operator, operand = fix_established(operator, operand)

        sql = VERSION_QUESTION_COUNT_SEARCH.format(operator, operand)

        self.env.cr.execute(sql)
        ids = self.env.cr.fetchall()

        return [('id', 'in', ids)]

    _sql_constraints = [
        (
            'unique_version_by_topic',
            'UNIQUE("name", "topic_id")',
            _('There is already another version with the first name')
        )
    ]

