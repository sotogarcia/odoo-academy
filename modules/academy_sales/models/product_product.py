# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger


_logger = getLogger(__name__)


class ProductProduct(models.Model):
    """ Links products with: training actions and training modules
    """

    _inherit = 'product.product'

    training_action_ids = fields.Many2many(
        string='Training actions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        relation='academy_training_action_product_product_rel',
        column1='product_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None
    )

    training_module_ids = fields.Many2many(
        string='Training modules',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.module',
        relation='academy_training_module_product_product_rel',
        column1='product_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None
    )
