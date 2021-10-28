# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ A student is a partner who can be enroled on training actions
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
        string='Student enrolments',
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

    enrolment_ids = fields.One2many(
        string='Enrolments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enrolments for this student',
        comodel_name='academy.training.action.enrolment',
        inverse_name='student_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
