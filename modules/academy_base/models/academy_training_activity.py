# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module contains the academy.training.activity Odoo model which stores
all training activity attributes and behavior.
"""

from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from .utils.custom_model_fields import Many2manyThroughView
from .utils.raw_sql import ACADEMY_TRAINING_ACTIVITY_TRAINING_MODULE_REL, \
    ACADEMY_TRAINING_ACTIVITY_TRAINING_UNIT_REL, \
    ACADEMY_TRAINING_ACTIVITY_AVAILABLE_RESOURCE_REL

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingActivity(models.Model):
    """ This describes the activity offered, its modules, training units
     and available resources.
    """

    _name = 'academy.training.activity'
    _description = u'Academy training activity'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = ['image.mixin', 'mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
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

    activity_code = fields.Char(
        string='Activity code',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Reference code that identifies the activity',
        size=30,
        translate=True
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

    available_module_ids = Many2manyThroughView(
        string='Training modules',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.module',
        relation='academy_training_activity_training_module_rel',
        column1='training_activity_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TRAINING_ACTIVITY_TRAINING_MODULE_REL
    )

    available_unit_ids = Many2manyThroughView(
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
        limit=None,
        sql=ACADEMY_TRAINING_ACTIVITY_TRAINING_UNIT_REL
    )

    activity_resource_ids = fields.Many2many(
        string='Activity resources',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_activity_training_resource_rel',
        column1='training_activity_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None
    )

    available_resource_ids = Many2manyThroughView(
        string='Available activity resources',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_activity_available_resource_rel',
        column1='training_activity_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TRAINING_ACTIVITY_AVAILABLE_RESOURCE_REL
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    @api.onchange('professional_field_id')
    def _onchange_professional_field_id(self):
        _id = self.professional_field_id.id
        domain = [('professional_field_id', '=', _id)]

        return {
            'domain': {
                'professional_sector_ids': domain
            }
        }

    # pylint: disable=W0212
    competency_unit_count = fields.Integer(
        string='Number of competency units',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute=lambda self: self._compute_competency_unit_count()
    )

    @api.depends('competency_unit_ids')
    def _compute_competency_unit_count(self):
        for record in self:
            record.competency_unit_count = len(record.competency_unit_ids)

    # pylint: disable=W0212
    training_action_count = fields.Integer(
        string='Number of training actions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        store=True,
        compute=lambda self: self._compute_training_action_count()
    )

    @api.depends('training_action_ids')
    def _compute_training_action_count(self):
        for record in self:
            record.training_action_count = len(record.training_action_ids)

    # pylint: disable=W0212
    training_resource_count = fields.Integer(
        string='Resources',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute=lambda self: self._compute_training_resource_count()
    )

    @api.depends('training_resource_ids')
    def _compute_training_resource_count(self):
        for record in self:
            record.training_resource_count = len(record.training_resource_ids)

    # ---------------------------- PUBLIC FIELDS ------------------------------

    # pylint: disable=locally-disabled, W0613
    def update_from_external(self, crud, fieldname, recordset):
        """ Observer notify method, will be called by action
        """
        self._compute_training_action_count()
