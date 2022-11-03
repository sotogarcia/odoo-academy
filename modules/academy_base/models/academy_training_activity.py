# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module contains the academy.training.activity Odoo model which stores
all training activity attributes and behavior.
"""

from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from .utils.libuseful import is_numeric, fix_established
from .utils.sql_inverse_searches import TRAINING_ACTION_COUNT_SEARCH

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingActivity(models.Model):
    """ This describes the activity offered, its modules and training units
    """

    _name = 'academy.training.activity'
    _description = u'Academy training activity'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = [
        'image.mixin',
        'ownership.mixin',
        'mail.thread',
        'mail.activity.mixin'
    ]

    state = fields.Selection(
        string='Status',
        required=True,
        readonly=False,
        index=True,
        default='draft',
        help='Crurrent record state',
        selection=[
            ('draft', 'Draft'),
            ('approve', 'Approved')
        ]
    )

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=1024,
        translate=True,
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

    activity_code = fields.Char(
        string='Activity code',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Reference code that identifies the activity',
        size=30,
        translate=False,
        tracking=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    professional_family_id = fields.Many2one(
        string='Professional family',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Professional family to which this activity belongs',
        comodel_name='academy.professional.family',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    professional_area_id = fields.Many2one(
        string='Professional area',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Professional area to which this activity belongs',
        comodel_name='academy.professional.area',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    qualification_level_id = fields.Many2one(
        string='Qualification level',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Qualification level to which this activity belongs',
        comodel_name='academy.qualification.level',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    general_competence = fields.Text(
        string='General competence',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=('Description of general competence that will be acquired at the '
              'end of the activity'),
        translate=True
    )

    professional_field_id = fields.Many2one(
        string='Professional field',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related professional field',
        comodel_name='academy.professional.field',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    professional_sector_ids = fields.Many2many(
        string='Professional sectors',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related professional sectors',
        comodel_name='academy.professional.sector',
        relation='academy_training_activity_professional_sector_rel',
        column1='training_activity_id',
        column2='professional_sector_id',
        domain=[],
        context={},
        limit=None
    )

    competency_unit_ids = fields.One2many(
        string='Competency units',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.competency.unit',
        inverse_name='training_activity_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    training_action_ids = fields.One2many(
        string='Training actions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Training actions in which this activity is imparted',
        comodel_name='academy.training.action',
        inverse_name='training_activity_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
    )

    available_module_ids = fields.Many2manyView(
        string='Training modules',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.module',
        relation='academy_competency_unit',
        column1='training_activity_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None,
    )

    available_unit_ids = fields.Many2manyView(
        string='Available training units',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.module',
        relation='academy_training_activity_training_unit_rel',
        column1='training_activity_id',
        column2='training_unit_id',
        domain=[],
        context={},
        limit=None
    )

    # This no needs an SQL statement
    training_module_ids = fields.Many2manyView(
        string='Modules',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Training activities in which module is used',
        comodel_name='academy.training.module',
        relation='academy_competency_unit',
        column1='training_activity_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    # pylint: disable=W0212
    competency_unit_count = fields.Integer(
        string='Number of competency units',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of competency units in the training activity',
        compute=lambda self: self._compute_competency_unit_count()
    )

    # The number of modules should be the same as the number of competencies
    # pylint: disable=W0212
    training_module_count = fields.Integer(
        string='Number of training modules',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of training modules in the training activity',
        compute=lambda self: self._compute_competency_unit_count()
    )

    @api.depends('competency_unit_ids')
    def _compute_competency_unit_count(self):
        for record in self:
            record.competency_unit_count = len(record.competency_unit_ids)
            record.training_module_count = record.competency_unit_count

    # pylint: disable=W0212
    training_action_count = fields.Integer(
        string='Number of training actions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        store=False,
        compute='_compute_training_action_count',
        search='_search_training_action_count'
    )

    @api.depends('training_action_ids')
    def _compute_training_action_count(self):
        for record in self:
            record.training_action_count = len(record.training_action_ids)

    @api.model
    def _search_training_action_count(self, operator, value):
        supported = ['=', '!=', '<=', '<', '>', '>=']

        assert operator in supported, \
            UserError(_('Search operator not supported'))

        assert is_numeric(value) or value in [True, False], \
            UserError(_('Search value not supported'))

        operator, value = fix_established(operator, value)

        sql = TRAINING_ACTION_COUNT_SEARCH.format(operator, value)

        self.env.cr.execute(sql)
        ids = self.env.cr.fetchall()

        return [('id', 'in', ids)]

    # -------------------------- MODEL CONTRAINTS -----------------------------

    _sql_constraints = [
        (
            'unique_activity_code',
            'UNIQUE("activity_code")',
            _('Another record with the same code already exists')
        )
    ]

    # -------------------------- OVERWRITTEN METHODS --------------------------

    @api.model
    def create(self, values):
        parent = super(AcademyTrainingActivity, self)
        result_set = parent.create(values)

        result_set._reconcile_training_actions_state(values)

        return result_set

    def write(self, values):
        parent = super(AcademyTrainingActivity, self)
        result = parent.write(values)

        self._reconcile_training_actions_state(values)

        return result

    def _reconcile_training_actions_state(self, values):
        state = values.get('state', False)

        if state == 'draft':
            enrolment_set = self.mapped('training_action_ids')
            enrolment_set.write({'state': state})

    # ---------------------------- PUBLIC FIELDS ------------------------------

    # pylint: disable=locally-disabled, W0613
    def update_from_external(self, crud, fieldname, recordset):
        """ Observer notify method, will be called by action
        """
        pass
        # self._compute_training_action_count()

    def show_training_actions(self):
        self.ensure_one()

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Training actions'),
            'res_model': 'academy.training.action',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': [('training_activity_id', '=', self.id)],
            'context': {
                'default_training_activity_id': self.id
            }
        }

    def show_competency_units(self):
        self.ensure_one()

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Competency units'),
            'res_model': 'academy.competency.unit',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': [('training_activity_id', '=', self.id)],
            'context': {
                'default_training_activity_id': self.id
            }
        }

    def show_training_modules(self):
        self.ensure_one()

        mids = self.mapped('competency_unit_ids.training_module_id.id')

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Training modules'),
            'res_model': 'academy.training.module',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', mids)],
            'context': {
                'default_training_activity_id': self.id
            }
        }
