# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingModule(models.Model):
    """ Links training actions to products
    """

    _inherit = ['academy.training.module']

    product_ids = fields.Many2many(
        string='Products',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='product.product',
        relation='academy_training_module_product_product_rel',
        column1='training_module_id',
        column2='product_id',
        domain=[],
        context={},
        limit=None
    )

    default_product_id = fields.Many2one(
        string='Default product',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='product.product',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('product_ids')
    def _onchange_product_ids(self):
        return {
            'domain': {
                'default_product_id': [('id', 'in', self.product_ids.ids)]
            }
        }
