# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Training Module

This module contains the academy.training.module an unique Odoo model
which contains all Academy Training Module attributes and behavior.

This model is the representation of the real life training module. This
is based on Spanish Certificate Training.

Classes:
    AcademyTrainingModule: This is the unique model class in this module
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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from .lib.custom_model_fields import Many2manyThroughView, \
    MODULE_INHERITED_RESOURCES_REL

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)





# pylint: disable=locally-disabled, R0903
class AcademyTrainingModule(models.Model):
    """ Coherent block of training associated with each of the competency units.

    Fields:
      name (Char): Human readable name which will identify each record.

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
        string='Own resources',
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
        sql=MODULE_INHERITED_RESOURCES_REL
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
        default=0.0, # pylint: disable=locally-disabled, W0212
        digits=(16, 2),
        help='Length in hours',
        compute=lambda self: self._compute_hours(), # pylint: disable=locally-disabled, W0212
    )

    @api.depends('training_unit_ids', 'ownhours')
    def _compute_hours(self):
        units_obj = self.env['academy.training.module']

        for record in self:
            units_domain = [('training_module_id', '=', record.id)]
            units_set = units_obj.search(units_domain, \
                offset=0, limit=None, order=None, count=False)

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
        lesson_set = lesson_obj.search(lesson_domain, \
            offset=0, limit=None, order=None, count=False)

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



