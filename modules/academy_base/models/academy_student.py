# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyStudent(models.Model):
    """ This model is the representation of the academy student
    """


    _name = 'academy.student'
    _description = u'Academy student'

    _inherit = ['mail.thread']
    _inherits = {'res.partner': 'res_partner_id'}


    res_partner_id = fields.Many2one(
        string='Partner',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    enrolment_ids = fields.One2many(
        string='Enrolments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action.enrolment',
        inverse_name='student_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
