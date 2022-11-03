# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.exceptions import ValidationError

from datetime import datetime
from dateutil.relativedelta import relativedelta


_logger = getLogger(__name__)


class AcademyDocumentAssignment(models.Model):
    ''' Allow to assign a file from dms to a training item
    '''

    _name = 'academy.document.assignment'
    _description = u'Allows you to assign documents to training elements'

    _rec_name = 'name'
    _order = 'name DESC'

    _inherit = [
        'ownership.mixin',
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
        translate=True
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
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it'),
        tracking=True
    )

    file_id = fields.Many2one(
        string='File',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Document will be assigned to',
        comodel_name='dms.file',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_ref = fields.Reference(
        string='Training',
        required=True,
        readonly=False,
        index=True,
        default=0,
        help='Training element: Enrolment, Action, Activity,...',
        selection=[
            ('academy.training.action.enrolment', 'Enrolment'),
            ('academy.training.action', 'Training action'),
            ('academy.training.activity', 'Training activity'),
            ('academy.competency.unit', 'Competency unit'),
            ('academy.training.module', 'Training module')
        ]
    )

    training_type = fields.Selection(
        string='Training type',
        required=True,
        readonly=False,
        index=True,
        default=False,
        help='Type of training: Enrolment, Action, Activity,...',
        selection=[
            ('academy.training.action.enrolment', 'Enrolment'),
            ('academy.training.action', 'Training action'),
            ('academy.training.activity', 'Training activity'),
            ('academy.competency.unit', 'Competency unit'),
            ('academy.training.module', 'Training module')
        ]
    )

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_module_id = fields.Many2one(
        string='Training module',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    secondary_id = fields.Many2one(
        string='Secondary',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    secondary_domain_id = fields.Many2one(
        string='Secondary domain',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_secondary_domain_id'
    )

    expiration = fields.Datetime(
        string='Expiration',
        required=True,
        readonly=False,
        index=True,
        default=datetime.now() + relativedelta(years=100),
        help='Date and time from which the file will be available'
    )

    @api.depends('training_ref')
    def _compute_secondary_domain_id(self):
        for record in self:
            training_ref = record.training_ref

            kind = getattr(training_ref, '_name', False)
            activity = getattr(training_ref, 'training_activity_id', False)

            if kind == 'academy.training.activity':
                record.secondary_domain_id = record.training_ref.id
            elif activity:
                record.secondary_domain_id = activity.id
            else:
                record.secondary_domain_id = None

    release = fields.Datetime(
        string='Release',
        required=True,
        readonly=False,
        index=True,
        default=fields.datetime.now(),
        help='Date and time from which the file will be available'
    )

    @api.onchange('training_ref')
    def _onchange_training_ref(self):
        self._reset_training()
        self._reconciliate_training()

    _sql_constraints = [
        (
            'mandaroty_training_ref',
            'CHECK(training_type IS NOT NULL AND training_ref IS NOT NULL)',
            _(u'You must set a training item')
        ),
        (
            'positive_available_interval',
            'CHECK(expiration > release)',
            _(u'Expiration date must be later than release date')
        ),
        (
            'single_assignment',
            'UNIQUE(file_id, training_ref)',
            _(u'Assignment of file to training is duplicated')
        ),
    ]

    @api.constrains('secondary_id')
    def _check_secondary_id(self):
        msg1 = _('Chosen training type does not contain competency units')
        msg2 = _('Chosen secondary training does not belong to the main one')

        for record in self:
            if not record.training_ref or not record.secondary_id:
                continue

            if not hasattr(record.training_ref, 'competency_unit_ids'):
                raise ValidationError(msg1)
            else:
                model = getattr(self.training_ref, '_name', False)
                code = self.training_ref.id

                related_id = self.env[model].browse(code)
                if record.secondary_id not in related_id.competency_unit_ids:
                    raise ValidationError(msg2)

    @api.depends('training_ref', 'file_id')
    def name_get(self):
        result = []

        display = self.env.context.get('name_get', None)
        pattern = _('Assigning file #{} to {} #{}')

        for record in self:
            if isinstance(record.id, models.NewId):
                name = _('New assignment')
            elif display == 'file':
                name = record.file_id.display_name
            elif display == 'training':
                name = record.training_ref.display_name
            else:
                training_type = record.get_training_type_name().lower()
                training_ref = record.training_ref.id
                file_id = record.file_id.id
                name = pattern.format(file_id, training_type, training_ref)

            result.append((record.id, name))

        return result

    def get_training_type_name(self):

        self.ensure_one()

        if self.training_ref:
            kind = getattr(self.training_ref, '_name', False)

            items = {
                'academy.training.action.enrolment': 'Enrolment',
                'academy.training.action': 'Training action',
                'academy.training.activity': 'Training activity',
                'academy.competency.unit': 'Competency unit',
                'academy.training.module': 'Training module'
            }

            result = items.get(kind, _('Unknown'))

        else:
            result = _('Not established')

        return result

    def _reset_training(self):
        self.ensure_one()

        self.training_type = None
        self.enrolment_id = None
        self.training_action_id = None
        self.training_activity_id = None
        self.competency_unit_id = None
        self.training_module_id = None
        self.secondary_id = None

    def _reconciliate_training(self):
        self.ensure_one()

        if self.training_ref:
            kind = getattr(self.training_ref, '_name', None)
            code = self.training_ref.id

            self.training_type = kind

            if kind == 'academy.training.action.enrolment':
                self.enrolment_id = self.env[kind].browse(int(code))
            elif kind == 'academy.training.action':
                self.training_action_id = self.env[kind].browse(int(code))
            elif kind == 'academy.training.activity':
                self.training_activity_id = self.env[kind].browse(int(code))
            elif kind == 'academy.competency.unit':
                self.competency_unit_id = self.env[kind].browse(int(code))
            elif kind == 'academy.training.module':
                self.training_module_id = self.env[kind].browse(int(code))

    @staticmethod
    def _reset_training_values(values):
        values['training_type'] = None
        values['enrolment_id'] = None
        values['training_action_id'] = None
        values['training_activity_id'] = None
        values['competency_unit_id'] = None
        values['training_module_id'] = None

        if 'training_ref' in values.keys():
            values['secondary_id'] = None

    @staticmethod
    def _reconciliate_training_values(values):
        ref = values.get('training_ref', False)

        if isinstance(ref, str) and ref and ref.count(',') == 1:
            kind, code = ref.split(',')
            values['training_type'] = kind

            if kind == 'academy.training.action.enrolment':
                values['enrolment_id'] = int(code)
            elif kind == 'academy.training.action':
                values['training_action_id'] = int(code)
            elif kind == 'academy.training.activity':
                values['training_activity_id'] = int(code)
            elif kind == 'academy.competency.unit':
                values['competency_unit_id'] = int(code)
            elif kind == 'academy.training.module':
                values['training_module_id'] = int(code)

    @api.model
    def create(self, values):

        parent = super(AcademyDocumentAssignment, self)

        self._reset_training_values(values)
        self._reconciliate_training_values(values)

        return parent.create(values)

    def write(self, values):

        parent = super(AcademyDocumentAssignment, self)

        self._reset_training_values(values)
        self._reconciliate_training_values(values)

        return parent.write(values)
