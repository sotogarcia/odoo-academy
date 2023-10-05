# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module contains the academy.training.action.enrolment Odoo model which
stores all training action enrolment attributes and behavior.
"""

from logging import getLogger
from datetime import datetime

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import ValidationError

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
        'mail.activity.mixin',
        'image.mixin',
        'academy.abstract.training',
        'ownership.mixin'
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
        tracking=True
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
        help='Enables/disables the record',
        tracking=True
    )

    company_id = fields.Many2one(
        string='Company',
        related='training_action_id.company_id'
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
        limit=None,
        tracking=True
    )

    # pylint: disable=locally-disabled, W0108
    register = fields.Date(
        string='Signup',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.context_today(self),
        help='Date in which student has been enrolled',
        tracking=True
    )

    deregister = fields.Date(
        string='Deregister',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Date in which student has been unsubscribed',
        tracking=True
    )

    training_modality_ids = fields.Many2many(
        string='Training modalities',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose training modalities',
        comodel_name='academy.training.modality',
        relation='academy_training_action_enrolment_training_modality_rel',
        column1='enrolment_id',
        column2='modality_id',
        domain=[],
        context={},
        limit=None,
        tracking=True
    )

    # This will be used in form view to compute domain
    available_modality_ids = fields.Many2many(
        string='Available modalities',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Available training modalities',
        comodel_name='academy.training.modality',
        relation='academy_training_action_enrolment_available_modalities_rel',
        column1='enrolment_id',
        column2='modality_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_available_modality_ids'
    )

    @api.depends('training_action_id')
    def _compute_available_modality_ids(self):
        modality_domain = []
        modality_obj = self.env['academy.training.modality']
        modality_set = modality_obj.search(modality_domain)

        for record in self:
            action = record.training_action_id
            if action and action.training_modality_ids:
                record.available_modality_ids = action.training_modality_ids
            else:
                record.available_modality_ids = modality_set

    # delivery = fields.Boolean(
    #     string='Materials were delivered',
    #     required=False,
    #     readonly=False,
    #     index=True,
    #     default=False,
    #     help='You have been given all the necessary material',
    #     tracking=True
    # )

    material = fields.Selection(
        string='Material',
        required=False,
        readonly=False,
        index=True,
        default='digital',
        help='Choose educational material format',
        selection=[
            ('printed', 'Printed'),
            ('digital', 'Digital')
        ]
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

    available_resource_ids = fields.Many2manyView(
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
        copy=False
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
        competency_path = ('training_action_id.training_activity_id.'
                           'competency_unit_ids.id')
        modality_path = 'training_action_id.training_modality_ids'

        for record in self:
            if self.training_action_id:
                unit_ids = record.mapped(competency_path)
                if unit_ids:
                    record.competency_unit_ids = [(6, 0, unit_ids)]

                self.training_modality_ids = self.mapped(modality_path)
                self.deregister = self.training_action_id.end
            else:
                record.competency_unit_ids = [(5, 0, 0)]
                self.training_modality_ids = None
                self.deregister = None

        competency_ids = self.mapped(competency_path)
        if competency_ids:
            competency_domain = [('id', 'in', competency_ids)]
        else:
            competency_domain = FALSE_DOMAIN

        modality_ids = self.mapped(modality_path + '.id')
        if modality_ids:
            modality_domain = [('id', 'in', modality_ids)]
        else:
            modality_domain = TRUE_DOMAIN

        return {
            'domain': {
                'competency_unit_ids': competency_domain,
                'training_modality_ids': modality_domain
            }
        }

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

    _sql_constraints = [
        (
            'check_date_order',
            'CHECK("deregister" IS NULL OR "register" <= "deregister")',
            _(u'End date must be greater then start date')
        ),
    ]

    @api.constrains('competency_unit_ids')
    def _check_competency_unit_ids(self):
        message = _('Enrolment must have at least one related competency unit')

        for record in self:
            if not record.competency_unit_ids:
                raise ValidationError(message)

    @api.constrains(
        'student_id', 'training_action_id', 'register', 'deregister')
    def _check_unique_enrolment(self):
        """
        """
        message = _('Student is already enrolled in the training action')
        enrolment_obj = self.env['academy.training.action.enrolment']

        for record in self:
            student_id = record.student_id.id
            action_id = record.training_action_id.id

            domains = [[('id', '<>', record.id)]]

            domains.append([('student_id', '=', student_id)])
            domains.append([('training_action_id', '=', action_id)])
            domains.append([
                '|',
                ('deregister', '=', False),
                ('deregister', '>', record.register)
            ])

            if not record.deregister:
                domains.append([('register', '<', record.deregister)])

            if enrolment_obj.search(AND(domains)):
                ValidationError(message)

    @api.model
    def _ensure_recordset(self, model, sources):
        source_obj = self.env[model]

        if isinstance(sources, int):
            source_set = source_obj.browse(sources)
        elif isinstance(sources, (list, tuple)):
            action_domain = [('id', 'in', sources)]
            source_set = source_obj.search(action_domain)
        else:
            msg = _('The source recordset must correspond to the model {}')
            assert isinstance(sources, type(source_obj)), msg.format(model)
            source_set = sources

        return source_set

    def copy_to(self, action_set, origin_set=False):

        if not origin_set:
            origin_set = self

        action_set = self._ensure_recordset(action_set)
        origin_set = self._ensure_recordset(origin_set or self)

        for enrolment in origin_set:

            for action in action_set:
                register = enrolment.register
                deregister = enrolment.deregister

                if register < action.start or register >= action.stop:
                    register = action.start

                if deregister > action.stop or deregister <= action.start or \
                   deregister <= register:
                    deregister = action.stop

                register = register.strftime('')
