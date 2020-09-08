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
