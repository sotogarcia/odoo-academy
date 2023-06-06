# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """
    """

    _inherit = ['academy.student']

    cefrl_ids = fields.Many2many(
        string='Languages',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='cefrl.certificate',
        relation='academy_student_cefrl_certificate_rel',
        column1='student_id',
        column2='certificate_id',
        domain=[],
        context={},
        limit=None
    )

    implied_cefrl_ids = fields.Many2many(
        string='Implied languages',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='cefrl.certificate',
        relation='academy_student_implied_cefrl_certificate_rel',
        column1='student_id',
        column2='certificate_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_implied_cefrl_ids',
        search='_search_implied_cefrl_ids'
    )

    @api.depends('cefrl_ids')
    def _compute_implied_cefrl_ids(self):
        for record in self:
            cefrl_set = record.mapped('cefrl_ids')
            cefrl_set += record.mapped('cefrl_ids.implied_ids')

            record.implied_cefrl_ids = cefrl_set

    @api.model
    def _search_implied_cefrl_ids(self, operator, value):

        return [
            '|',
            ('cefrl_ids', operator, value),
            ('cefrl_ids.implied_ids', operator, value)
        ]
