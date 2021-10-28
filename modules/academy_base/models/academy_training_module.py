# -*- coding: utf-8 -*-
""" AcademyTrainingModule

This module contains the academy.training.module Odoo model which stores
all training module attributes and behavior.
"""

from odoo import models, fields, api

from .utils.custom_model_fields import Many2manyThroughView
from .utils.raw_sql import ACADEMY_TRAINING_MODULE_AVAILABLE_RESOURCE_REL, \
    ACADEMY_TRAINING_MODULE_USED_IN_TRAINING_ACTION_REL

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingModule(models.Model):
    """ A module is a piece of training which can be can be used in serveral
    training activities at the same time
    """

    _name = 'academy.training.module'
    _description = u'Academy training module'

    _inherit = ['image.mixin', 'mail.thread']

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

    module_code = fields.Char(
        string='Code',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter code for training module',
        size=30,
        translate=True,
        old_name='code'
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

    available_resource_ids = Many2manyThroughView(
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
        sql=ACADEMY_TRAINING_MODULE_AVAILABLE_RESOURCE_REL
    )

    used_in_action_ids = Many2manyThroughView(
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
        sql=ACADEMY_TRAINING_MODULE_USED_IN_TRAINING_ACTION_REL
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Choose the unit order'
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
        help='Number of training units in module',
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

    # --------------------------- PUBLIC METHODS ------------------------------

    def get_imparted_hours_in(self, action_id):
        """ Get all hours assigned an a given action (id) for this recordset

        @param action_id (recordset/int) : academy.training.action record or id

        @return (float): total time length
        """

        result = 0

        for record in self:
            result = result + self.get_imparted_hours_for(action_id, record.id)

        return result

    @api.model
    def get_imparted_hours_for(self, action_id, module_id):
        """ Get all hours assigned for given module (id) an a given action (id)

        @param action_id (recordset/int): academy.training.action record or id
        @param module_id (recordset/int): academy.training.module record or id

        @return (float): total time length
        """

        action_id = self._get_id(action_id) or -1
        module_id = self._get_id(module_id) or -1

        lesson_domain = [
            '&',
            ('training_action_id', '=', action_id),
            ('training_module_id', '=', module_id),
        ]

        lesson_obj = self.env['academy.training.lesson']
        lesson_set = lesson_obj.search(
            lesson_domain, offset=0, limit=None, order=None, count=False)

        return sum(lesson_set.mapped('duration') or [0])

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
