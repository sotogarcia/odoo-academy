# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsRandomTemplateTrainingActionRel(models.Model):
    """ Many2many relationship with sequence
    """

    _name = 'academy.tests.random.template.training.action.rel'
    _description = u'Academy tests random template training action relationship'

    _rec_name = 'random_template_id'
    _order = 'training_action_id ASC, sequence ASC'

    training_action_id = fields.Many2one(
        string='Training action',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose training action',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    random_template_id = fields.Many2one(
        string='Template',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose random test template',
        comodel_name='academy.tests.random.template',
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
        help='Preference order for this template'
    )
