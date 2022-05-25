# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class SaleOrderLine(models.Model):
    """ Links sale order line to an action enrolment
    """

    _inherit = ['sale.order.line']

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Enrolment binded to this sale order line',
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='set null',
        auto_join=False
    )
