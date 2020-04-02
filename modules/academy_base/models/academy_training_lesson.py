# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Training Lesson

This module contains the academy.training.lesson an unique Odoo model
which contains all Academy Training Lesson attributes and behavior.

This model is the representation of the real life training lesson. One
lesson has some related resources and a linked list of students who have
attended.

In addition, training you can designate the modules or units which have
been imparted in it.

Classes:
    AcademyTrainingLesson: This is the unique model class in this module
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
class AcademyTrainingLesson(models.Model):
    """ This model is the representation of the real life training lesson. One
lesson has some related resources and a linked list of students who have
attended.

    Fields:
      name (Char)       : Human readable name which will identify each record
      description (Text): Something about the record or other information witch
      has not an specific defined field to store it.
      active (Boolean)  : Checked do the record will be found by search and
      browse model methods, unchecked hides the record.

    """


    _name = 'academy.training.lesson'
    _description = u'Academy training lesson'

    _inherits = {
        'academy.training.action' : 'training_action_id',
        'academy.training.module' : 'training_module_id'
    }

    _rec_name = 'code'
    _order = 'code ASC'

    _inherit = ['mail.thread']


    training_action_id = fields.Many2one(
        string='Training action',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Choose the related training action',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_module_id = fields.Many2one(
        string='Training module',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    # pylint: disable=locally-disabled, W0212
    code = fields.Char(
        string='Lesson ID',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self._default_code(),
        help='Enter new name',
        size=12,
        translate=True,
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    start_date = fields.Datetime(
        string='Start date/time',
        required=True,
        readonly=False,
        index=False,
        default=fields.datetime.now(),
        help='Start lesson date/time'
    )

    duration = fields.Float(
        string='Date delay',
        required=True,
        readonly=False,
        index=False,
        default=2.0,
        digits=(16, 2),
        help="Time length of the lesson"
    )

    teacher_id = fields.Many2one(
        string='Teacher',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the teacher who expound the lesson',
        comodel_name='academy.teacher',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_resource_ids = fields.Many2many(
        string='Training resources',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_resource_lesson_rel',
        column1='training_lesson_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None
    )

    # -------------------------------------------------------------------------


    @api.model
    def _default_code(self):
        """ Get next value for sequence
        """

        seqxid = 'academy_base.ir_sequence_academy_lesson'
        seqobj = self.env.ref(seqxid)

        result = seqobj.next_by_id()

        return result


    @api.onchange('training_module_id')
    def _onchange_training_module_id(self):
        module_set = self.training_module_id
        res_list = []

        for res in module_set.training_resource_ids:
            res_list.append((4, res.id, None))

        for res in module_set.available_training_resource_ids:
            res_list.append((4, res.id, None))

        self.training_resource_ids = res_list


    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):
        if self.training_action_id:
            ids = self.training_action_id.training_unit_ids.mapped('id')
            domain = [('id', 'in', ids)]
        else:
            domain = [('id', '=', -1)]

        return {
            'domain': {
                'training_module_id': domain
            }
        }
