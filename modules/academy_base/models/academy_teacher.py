# -*- coding: utf-8 -*-
""" AcademyTeacher

This module contains the academy.teacher Odoo model which stores
all teacher attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTeacher(models.Model):
    """ Teachers are Odoo users who can perform some limited actions over
    academy records
    """

    _name = 'academy.teacher'
    _description = u'Academy teacher'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = ['mail.thread']
    _inherits = {'res.users': 'res_users_id'}

    res_users_id = fields.Many2one(
        string='Platform user',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_unit_ids = fields.Many2many(
        string='Training units',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related training units',
        comodel_name='academy.training.module',
        relation='academy_training_module_teacher_rel',
        column1='teacher_id',
        column2='training_module_id',
        domain=[
            '|',
            ('training_module_id', '=', False),
            ('training_unit_ids', '=', False)
        ],
        context={},
        limit=None
    )

    training_lesson_ids = fields.One2many(
        string='Training lessons',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.lesson',
        inverse_name='teacher_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
