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

    order_line_ids = fields.One2many(
        string='Order lines',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Sale order lines for this enrolment',
        comodel_name='sale.order.line',
        inverse_name='enrolment_id',
        domain=[],
        context={},
        auto_join=False,
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
