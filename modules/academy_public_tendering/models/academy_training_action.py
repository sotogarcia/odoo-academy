# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Training Action

Classes:
    AcademyTrainingAction: This model extends academy.training.action model
    from academy_base module

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingAction(models.Model):
    """ This model extends academy.training.action model from academy_base
    module
    """

    _name = 'academy.training.action'
    _inherit = 'academy.training.action'

    public_tendering_process_ids = fields.Many2many(
        string='Public tendering process',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.public.tendering.process',
        relation='academy_training_action_public_tendering_process_rel',
        column1='training_action_id',
        column2='public_tendering_id',
        domain=[],
        context={},
        limit=None
    )
