# -*- coding: utf-8 -*-
""" AcademyTeacher

This module contains the academy.teacher Odoo model which stores
all teacher attributes and behavior.
"""

from odoo import models, fields, api

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingLesson(models.Model):
    """ Lesson represents a period of instruction. It links a student to a
    training module over a period of time
    """

    _name = 'academy.training.lesson'
    _description = u'Academy training lesson'

    _inherits = {
        'academy.training.action': 'training_action_id',
        'academy.training.module': 'training_module_id'
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
        string='Lesson module',
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
        size=30,
        translate=False,
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
        string='Duration',
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
        string='Lesson resources',
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

        for res in module_set.module_resource_ids:
            res_list.append((4, res.id, None))

        for res in module_set.available_resource_ids:
            res_list.append((4, res.id, None))

        self.training_resource_ids = res_list

    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):
        if self.training_action_id:
            ids = self.training_action_id.available_unit_ids.mapped('id')
            domain = [('id', 'in', ids)]
        else:
            domain = [('id', '=', -1)]

        return {
            'domain': {
                'training_module_id': domain
            }
        }
