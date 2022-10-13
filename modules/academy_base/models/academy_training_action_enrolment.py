# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module contains the academy.training.action.enrolment Odoo model which
stores all training action enrolment attributes and behavior.
"""

from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.osv.expression import FALSE_DOMAIN

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

    _inherit = [
        'mail.thread',
        'image.mixin',
        'academy.abstract.training',
        'academy.abstract.owner'
    ]

    # pylint: disable=locally-disabled, W0212
    code = fields.Char(
        string='Code',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self._default_code(),
        help='Enter new code',
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

    competency_unit_ids = fields.Many2many(
        string='Competency units',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Choose competency units in which the student will be enrolled',
        comodel_name='academy.competency.unit',
        relation='academy_action_enrolment_competency_unit_rel',
        column1='action_enrolment_id',
        column2='competency_unit_id',
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
        readonly=True,
        help='Show the name of the related student',
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

    enrolment_resource_ids = fields.Many2many(
        string='Enrolment resources',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_action_enrolment_training_resource_rel',
        column1='enrolment_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None
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

    finalized = fields.Boolean(
        string='Finalized',
        required=True,
        readonly=True,
        index=False,
        default=False,
        help='True if period is completed',
        compute='_compute_finalized',
        search='_search_finalized',
    )

    email = fields.Char(
        string='Email',
        related='student_id.res_partner_id.email'
    )

    phone = fields.Char(
        string='Phone',
        related='student_id.res_partner_id.phone'
    )

    zip = fields.Char(
        string='Zip',
        related='student_id.res_partner_id.zip'
    )

    action_name = fields.Char(
        string='Action name',
        help='Enter new name',
        related="training_action_id.action_name"
    )

    action_code = fields.Char(
        string='Internal code',
        help='Enter new internal code',
        related="training_action_id.action_code"
    )

    start = fields.Datetime(
        string='Start',
        help='Start date of an event, without time for full day events',
        related="training_action_id.start"
    )

    end = fields.Datetime(
        string='End',
        help='Stop date of an event, without time for full day events',
        related="training_action_id.end"
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        help='Training activity will be imparted in this action',
        related="training_action_id.training_activity_id"
    )

    image_1024 = fields.Image(
        string="Image 1024",
        related="training_action_id.image_1024",
    )

    image_512 = fields.Image(
        string="Image 512",
        related="training_action_id.image_512",
    )

    image_256 = fields.Image(
        string="Image 256",
        related="training_action_id.image_256",
    )

    image_128 = fields.Image(
        string="Image 128",
        related="training_action_id.image_128",
    )

    @api.depends('register', 'deregister')
    def _compute_finalized(self):
        now = fields.Date.today()
        for record in self:
            record.finalized = record.deregister and record.deregister < now

    def _search_finalized(self, operator, value):
        pattern = _('Unsupported domain leaf ("finalized", "{}", "{}")')
        now = fields.Date.to_string(fields.Date.today())

        if operator == '!=':
            operator == '<>'

        if (operator == '=' and value) or (operator == '<>' and not value):
            domain = [
                '&',
                ('deregister', '<>', False),
                ('deregister', '<', now)
            ]

        elif (operator == '=' and not value) or (operator == '<>' and value):
            domain = [
                '|',
                ('deregister', '=', False),
                ('deregister', '>=', now)
            ]

        else:
            raise UserError(pattern.format(operator, value))

        return domain

    # ---------------------------- ONCHANGE EVENTS ----------------------------

    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):
        path = 'training_action_id.training_activity_id.competency_unit_ids.id'

        for record in self:
            record.competency_unit_ids = [(5, 0, 0)]

            unit_ids = record.mapped(path)
            if unit_ids:
                record.competency_unit_ids = [(6, 0, unit_ids)]

        competency_ids = self.mapped(path)
        if competency_ids:
            domain = [('id', 'in', competency_ids)]
        else:
            domain = FALSE_DOMAIN

        return {'domain': {'competency_unit_ids': domain}}

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
            if record.student_id and record.training_action_id:
                training = record.training_action_id.action_name
                student = record.student_id.name

                name = '{} - {}'.format(training, student)

            else:
                name = _('New training action enrolment')

            result.append((record.id, name))

        return result

    def go_to_student(self):
        student_set = self.mapped('student_id')

        if not student_set:
            msg = _('There is no students')
            raise UserError(msg)
        else:

            view_act = {
                'type': 'ir.actions.act_window',
                'res_model': 'academy.student',
                'target': 'current',
                'nodestroy': True,
                'domain': [('id', 'in', student_set.mapped('id'))]
            }

            if len(student_set) == 1:
                view_act.update({
                    'name': student_set.name,
                    'view_mode': 'form,kanban,tree',
                    'res_id': student_set.id,
                    'view_type': 'form'
                })

            else:
                view_act.update({
                    'name': _('Students'),
                    'view_mode': 'tree',
                    'res_id': None,
                    'view_type': 'form'
                })

            return view_act
