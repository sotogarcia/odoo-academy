# -*- coding: utf-8 -*-
""" AcademyTrainingModule

This module contains the academy.training.module Odoo model which stores
all training module attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingModule(models.Model):
    """ A module is a piece of training which can be can be used in serveral
    training activities at the same time
    """

    _name = 'academy.training.module'
    _description = u'Academy training module'

    _inherit = [
        'image.mixin',
        'mail.thread',
        'academy.abstract.training',
        'ownership.mixin'
    ]

    _rec_name = 'name'
    _order = 'name ASC'

    # ---------------------------- ENTITY FIELDS ------------------------------

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=1024,
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
        help='Enables/disables the record'
    )

    training_module_id = fields.Many2one(
        string='Training module',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Parent module',
        comodel_name='academy.training.module',
        domain=[('training_module_id', '=', False)],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_unit_ids = fields.One2many(
        string='Training units',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Training units in this module',
        comodel_name='academy.training.module',
        inverse_name='training_module_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    competency_unit_ids = fields.One2many(
        string='Competency units',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='List all competency units which use this training module',
        comodel_name='academy.competency.unit',
        inverse_name='training_module_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    tree_ids = fields.Many2manyView(
        string='Module tree',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List this module and all its training units',
        comodel_name='academy.training.module',
        relation='academy_training_module_tree_readonly',
        column1='requested_module_id',
        column2='responded_module_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    module_code = fields.Char(
        string='Code',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter code for training module',
        size=30,
        translate=False,
    )

    ownhours = fields.Float(
        string='Own hours',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Length in hours'
    )

    module_resource_ids = fields.Many2many(
        string='Module resources',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_module_training_resource_rel',
        column1='training_module_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None
    )

    available_resource_ids = fields.Many2manyView(
        string='Available resources',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_module_available_resource_rel',
        column1='training_module_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    used_in_action_ids = fields.Many2manyView(
        string='Used in actions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        relation='academy_training_module_used_in_training_action_rel',
        column1='training_module_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Choose the unit order'
    )

    # This no needs an SQL statement
    training_activity_ids = fields.Many2manyView(
        string='Activities',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Training activities in which module is used',
        comodel_name='academy.training.activity',
        relation='academy_competency_unit',
        column1='training_module_id',
        column2='training_activity_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    # --------------------------- COMPUTED FIELDS -----------------------------

    hours = fields.Float(
        string='Hours',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Length in hours',
        compute=lambda self: self._compute_hours()
    )

    @api.depends('training_unit_ids', 'ownhours')
    def _compute_hours(self):
        units_obj = self.env['academy.training.module']

        for record in self:
            units_domain = [('training_module_id', '=', record.id)]
            units_set = units_obj.search(
                units_domain, offset=0, limit=None, order=None, count=False)

            if units_set:
                record.hours = sum(units_set.mapped('ownhours'))
            else:
                record.hours = record.ownhours

    training_unit_count = fields.Integer(
        string='Units',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of training units in the training module',
        compute='_compute_training_unit_count',
    )

    @api.depends('training_unit_ids')
    def _compute_training_unit_count(self):
        for record in self:
            record.training_unit_count = len(record.training_unit_ids)

    # ----------------- AUXILIARY FIELD METHODS AND EVENTS --------------------

    @api.model
    def create(self, values):
        """ Updates sequence field after create
        """

        result = super(AcademyTrainingModule, self).create(values)

        return result

    # -------------------------- AUXILIARY METHODS ----------------------------

    def _get_id(self, model_or_id):
        """ Returns a valid id or rises an error
        """
        if isinstance(model_or_id, int):
            result = model_or_id
        else:
            self.ensure_one()
            result = model_or_id.id

        return result

    def view_training_units(self):
        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Training units'),
            'res_model': 'academy.training.module',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': [('training_module_id', '=', self.id)],
            'context': {
                'default_training_module_id': self.id
            }
        }
