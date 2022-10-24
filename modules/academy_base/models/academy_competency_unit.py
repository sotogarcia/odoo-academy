# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module contains the academy.competency.unit Odoo model which stores
all competency unit attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyCompetencyUnit(models.Model):
    """ Competency unit stores the specific name will be used by a module in
    a training activity
    """

    _name = 'academy.competency.unit'
    _description = u'Academy competency unit'

    _rec_name = 'competency_name'
    _order = ('sequence ASC, competency_name ASC')

    _inherits = {'academy.training.module': 'training_module_id'}

    _inherit = [
        'academy.abstract.training',
        'mail.thread',
        'mail.activity.mixin'
    ]

    competency_code = fields.Char(
        string='Unit code',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Reference code that identifies the competency unit',
        size=30,
        translate=False
    )

    competency_name = fields.Char(
        string='Competency name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=1024,
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

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Choose this competency unit order position'
    )

    training_module_id = fields.Many2one(
        string='Training module',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Training module associated with this competency unit',
        comodel_name='academy.training.module',
        domain=[('training_module_id', '=', False)],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    professional_qualification_id = fields.Many2one(
        string='Academy professional qualification',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.professional.qualification',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    competency_unit_resource_ids = fields.Many2many(
        string='Competency unit resources',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_competency_unit_training_resource_rel',
        column1='competency_unit_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None
    )

    # -------------------------- OVERLOADED METHODS ---------------------------

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Prevents new record of the inherited (_inherits) model will be
        created
        """

        default = dict(default or {})
        default.update({
            'training_module_id': self.training_module_id.id
        })

        rec = super(AcademyCompetencyUnit, self).copy(default)
        return rec

    def view_details(self):
        self.ensure_one()

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': self.competency_name,
            'res_model': 'academy.competency.unit',
            'target': 'current',
            'view_mode': 'form',
            'res_id': self.id,
            'domain': [],
            'context': {}
        }

    # -------------------------- MODEL CONTRAINTS -----------------------------

    _sql_constraints = [
        (
            'unique_competency_code',
            'UNIQUE("competency_code")',
            _('Another record with the same code already exists')
        ),
        (
            'unique_module_by_activity',
            'UNIQUE("training_activity_id", "training_module_id")',
            _('Another competency has the same module in this activity')
        ),
        (
            'unique_competency_name_by_activity',
            'UNIQUE("training_activity_id", "competency_name")',
            _('Another record with the same name already exists')
        )
    ]
