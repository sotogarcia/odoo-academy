# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################


from odoo import models, fields, api
from odoo.tools.translate import _


from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTopicTrainingModuleLink(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.topic.training.module.link'
    _description = u'Academy tests, topic-training module link'

    _rec_name = 'topic_id'
    _order = 'topic_id ASC'


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

    training_module_id = fields.Many2one(
        string='Training module',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Module will be linked to the topic',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    category_ids = fields.Many2many(
        string='Categories',
        required=False,
        readonly=False,
        index=False,
        default=None,
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


    @api.onchange('topic_id')
    def _onchange_academy_topid_id(self):
        """ Updates domain form category_ids, this shoud allow categories
        only in the selected topic.
        """
        topic_set = self.topic_id
        valid_ids = topic_set.category_ids & self.category_ids

        self.category_ids = [(6, None, valid_ids.mapped('id'))]

    _sql_constraints = [
        (
            'unique_topic_id_training_module_id',
            'UNIQUE(topic_id, training_module_id)',
            _(u'Each topic can only be linked once')
        )
    ]
