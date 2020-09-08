# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.action.enrolment Odoo model which stores
all training action attributes and behavior.

"""

from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from .lib.custom_model_fields import Many2manyThroughView, \
    ACTION_EHROLMENT_INHERITED_RESOURCES_REL


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingActionEnrolment(models.Model):
    """ This model stores attributes and behavior relative to the
    enrollment of students in academy training actions
    """

    _name = 'academy.training.action.enrolment'
    _description = u'Academy training action enrolment'

    _rec_name = 'code'
    _order = 'code ASC'

    _inherits = {
        'academy.student': 'student_id',
        'academy.training.action': 'training_action_id'
    }

    _inherit = ['mail.thread']


    # pylint: disable=locally-disabled, W0212
    code = fields.Char(
        string='Code',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self._default_code(),
        help='Enter new code',
        size=30,
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

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose enrolled student',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose training action in which the student will be enrolled',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    # pylint: disable=locally-disabled, W0212
    training_module_ids = fields.Many2many(
        string='Training modules',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose modules in which the student will be enrolled',
        comodel_name='academy.training.module',
        relation='academy_action_enrolment_training_module_rel',
        column1='action_enrolment_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None
    )

    # pylint: disable=locally-disabled, W0108
    register = fields.Date(
        string='Sign up',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.context_today(self),
        help='Date in which student has been enrolled'
    )

    deregister = fields.Date(
        string='Deregister',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Date in which student has been unsubscribed'
    )

    student_name = fields.Char(
        string='Student name',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show the name of the related student',
        size=255,
        translate=True,
        compute=lambda self: self._compute_student_name()
    )


    available_resource_ids = Many2manyThroughView(
        string='Training resources',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_action_enrolment_available_resource_rel',
        column1='enrolment_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None,
        sql=ACTION_EHROLMENT_INHERITED_RESOURCES_REL
    )

    @api.depends('student_id')
    def _compute_student_name(self):
        for record in self:
            record.student_name = record.student_id.name


    # ---------------------------- ONCHANGE EVENTS ----------------------------


    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):
        action_set = self.training_action_id
        activity_set = action_set.mapped('training_activity_id')
        competency_set = activity_set.mapped('competency_unit_ids')
        module_set = competency_set.mapped('training_module_id')
        ids = module_set.ids

        self.training_module_ids = module_set

        if module_set:
            domain = {'training_module_ids': [('id', 'in', ids)]}
            return {'domain': domain}

        return {'domain': {'training_module_ids': [('id', '=', -1)]}}


    # -------------------------- OVERLOADED METHODS ---------------------------


    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Prevents new record of the inherited (_inherits) models will
        be created. It also adds the following sequence value.
        """

        default = dict(default or {})
        default.update({
            'student_id': self.student_id.id,
            'training_action_id': self.training_action_id.id,
            'code': self._default_code()
        })

        rec = super(AcademyTrainingActionEnrolment, self).copy(default)
        return rec


    # -------------------------- PYTHON CONSTRAINTS ---------------------------


    # @api.constrains('training_action_id', 'student_id')
    # def _check_unique_enrolment(self):

    #     action_id = self.training_action_id.id or -1
    #     student_id = self.student_id.id or -1

    #     domain = [
    #         ('training_action_id', '=', action_id),
    #         ('student_id', '=', student_id),
    #         ('deregister', '=', False),
    #         ('id', '<>', self.id)
    #     ]
    #     enroled_set = self.search(domain)

    #     if enroled_set.competency_unit_ids & self.competency_unit_ids:
    #         msg = _('{} already has been enrolled in same '
    #                 'competency units for {}')
    #         msg = msg.format(
    #             self.student_id.name,
    #             self.training_action_id.action_name
    #         )
    #         raise ValidationError(msg)


    # -------------------------- AUXILIARY METHODS ----------------------------


    @api.model
    def _default_code(self):
        """ Get next value for sequence
        """

        seqxid = 'academy_base.ir_sequence_academy_action_enrolment'
        seqobj = self.env.ref(seqxid)

        result = seqobj.next_by_id()

        return result





