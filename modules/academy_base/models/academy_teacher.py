# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Teacher

This module contains the academy.teacher an unique Odoo model
which contains all Academy Teacher attributes and behavior.

This model is the representation of the real life academy teacher

Classes:
    AcademyTeacher: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

    Inside this class can be, in order, the following attributes and methods:
    * Object attributes like name, description, inheritance, etc.
    * Entity fields with the full definition
    * Computed fields and required computation methods
    * Events (@api.onchange) and other field required methods like computed
    domain, defaul values, etc...
    * Overloaded object methods, like create, write, copy, etc.
    * Public object methods will be called from outside
    * Private auxiliary methods not related with the model fields, they will
    be called from other class methods


Todo:
    * Complete the model attributes and behavior

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.exceptions import ValidationError


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTeacher(models.Model):
    """ This model is the representation of the academy teacher
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
