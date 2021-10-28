# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module contains the academy.training.action.enrolment Odoo model which
stores all training action enrolment attributes and behavior.
"""

from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _

from .utils.custom_model_fields import Many2manyThroughView
from .utils.raw_sql import \
    ACADEMY_TRAINING_ACTION_ENROLMENT_AVAILABLE_RESOURCE_REL


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingActionEnrolment(models.Model):
    """ Enrollment allows the student to be linked to a training action
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
        string='Enrolled in the modules',
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
        string='Signup',
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

    # It is necessary to keep the difference with the name of the activity
    student_name = fields.Char(
        string='Student name',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show the name of the related student',
        size=255,
        translate=True,
        related="student_id.name"
    )

    # It is necessary to keep the difference with the name of the activity
    action_name = fields.Char(
        string='Training action name',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show the name of the related training action',
        size=255,
        translate=True,
        related="training_action_id.action_name"
    )

    available_resource_ids = Many2manyThroughView(
        string='Available enrolment resources',
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
        sql=ACADEMY_TRAINING_ACTION_ENROLMENT_AVAILABLE_RESOURCE_REL
    )

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

    # -------------------------- AUXILIARY METHODS ----------------------------

    @api.model
    def _default_code(self):
        """ Get next value for sequence
        """

        seqxid = 'academy_base.ir_sequence_academy_action_enrolment'
        seqobj = self.env.ref(seqxid)

        result = seqobj.next_by_id()

        return result

    def name_get(self):
        result = []

        for record in self:
            student = record.student_id.name
            if len(record.training_module_ids) == 1:
                item = record.training_module_ids.name
            else:
                item = record.training_action_id.name

            if student and item:
                name = '{} - {}'.format(item, student)
            else:
                name = _('New training action enrolment')

            result.append((record.id, name))

        return result
