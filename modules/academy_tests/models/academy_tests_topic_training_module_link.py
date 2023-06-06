# -*- coding: utf-8 -*-
""" AcademyTestsTopicTrainingModuleLink

This module contains the academy.tests.topic.training.module.link
Odoo model which stores all needed attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)

TOPIC_VERSION_IDS_TABLE = \
    'academy_tests_topic_version_topic_training_module_link_rel'


class AcademyTestsTopicTrainingModuleLink(models.Model):
    """ This model make possible a relationship between academy.training.module
    academy.tests.topic and academy.tests.category.
    """

    _name = 'academy.tests.topic.training.module.link'
    _description = u'Academy tests, topic-training module link'

    _rec_name = 'topic_id'
    _order = 'topic_id ASC'

    training_module_id = fields.Many2one(
        string='Training module',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Module will be linked to the topic',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Topic will be linked to the module',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    topic_version_id = fields.Many2one(
        string='Topic version',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_topic_version_id(),
        help='Version in topic will be linked to the module',
        comodel_name='academy.tests.topic.version',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    category_ids = fields.Many2many(
        string='Category list',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_category_ids(),
        help='Categories relating to this question',
        comodel_name='academy.tests.category',
        relation='academy_tests_category_tests_topic_training_module_link_rel',
        column1='tests_topic_training_module_link_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None,
        track_visibility='onchange',
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Choose the unit order'
    )

    category_count = fields.Integer(
        string='Number of categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of chosen categories',
        store=False,
        compute=lambda self: self.compute_category_count()
    )

    question_ids = fields.Many2manyView(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all questions that match the chosen topics and categories',
        comodel_name='academy.tests.question',
        relation='academy_tests_topic_training_module_link_question_rel',
        column1='topic_module_link_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    question_count = fields.Integer(
        string='Nº questions',
        required=True,
        readonly=True,
        index=False,
        default=0,
        store=False,
        help='Show the number of related questions',
        compute='_compute_question_count'
    )

    @api.depends('question_ids')
    def _compute_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)

    _sql_constraints = [
        (
            'unique_topic_id_training_module_id',
            'UNIQUE(topic_id, training_module_id)',
            _(u'Each topic can only be linked once')
        )
    ]

    @api.depends('category_ids')
    def compute_category_count(self):
        for record in self:
            record.category_count = len(record.category_ids)

    @api.onchange('topic_id')
    def _onchange_topic_id(self):
        for record in self:
            record.topic_version_id = record.default_topic_version_id()
            record.category_ids = record.default_category_ids()

        self.compute_category_count()

    def default_topic_version_id(self):
        """ Computes default value for the topic version Many2many field, this
        will be the last version.

        Returns:
            mixed -- versions will be added or None
        """

        topic_version_ids = self.topic_id.topic_version_ids.sorted(
            lambda x: x.sequence, reverse=True)

        return topic_version_ids[0] if topic_version_ids else None

    def default_category_ids(self):
        """ Computes default value for the category Many2many field.

        If chosen topic has few categories all of them will be added, the
        field value will be empty if there are too many.

        Returns:
            mixed -- categories will be added or None
        """

        length = len(self.topic_id.category_ids)
        return self.topic_id.category_ids if length <= 3 else None

    @api.depends('topic_id', 'training_module_id')
    def name_get(self):
        pattern = _('Training module {}')
        result = []

        for link in self:
            if isinstance(link.id, models.NewId):
                name = _('New link')
            else:
                module = link.training_module_id
                code = module.module_code or pattern.format(module.id)
                name = '{} - {}'.format(code, link.topic_id.name)
                result.append((link.id, name))

        return result
