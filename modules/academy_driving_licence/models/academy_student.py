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

    driving_ids = fields.Many2many(
        string='Driving licences',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Driving licences obtained by the student',
        comodel_name='driving.licence',
        relation='academy_student_driving_licence_rel',
        column1='student_id',
        column2='license_id',
        domain=[],
        context={},
        limit=None
    )

    implied_driving_ids = fields.Many2many(
        string='Implied driving licences',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Driving licences recognized to the student',
        comodel_name='driving.licence',
        relation='academy_student_implied_driving_licence_rel',
        column1='student_id',
        column2='license_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_implied_driving_ids',
        search='_search_implied_driving_ids'
    )

    @api.depends('driving_ids')
    def _compute_implied_driving_ids(self):
        for record in self:
            driving_set = record.mapped('driving_ids')
            driving_set += record.mapped('driving_ids.implied_ids')

            record.implied_driving_ids = driving_set

    @api.model
    def _search_implied_driving_ids(self, operator, value):

        return [
            '|',
            ('driving_ids', operator, value),
            ('driving_ids.implied_ids', operator, value)
        ]
