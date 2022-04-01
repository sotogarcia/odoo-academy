# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionEnrolment(models.Model):
    """ Links training actions to products
    """

    _inherit = ['academy.training.action.enrolment']

    product_id = fields.Many2one(
        string='Product',
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

    sale_ids = fields.Many2many(
        string='Sales',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Service sales for this enrolment',
        comodel_name='sale.order',
        relation='academy_training_action_enrolment_sale_order_rel',
        column1='enrolment_id',
        column2='sale_order_id',
        domain=[],
        context={},
        limit=None
    )

    def invoice(self):
        for record in self:
            pass

    def renew(self):
        for record in self:
            pass

    def prorogate(self):
        for record in self:
            pass

    def renounce(self):
        for record in self:
            pass
