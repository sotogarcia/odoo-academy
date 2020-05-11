# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module contains the academy.competency.unit Odoo model which stores
all competency.unit attributes and behavior.

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api


# pylint: disable=locally-disabled, c0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyCompetencyUnit(models.Model):
    """ Minimum set of professional skills, capable of recognition and partial
    accreditation.

    Fields:
      competency_name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.competency.unit'
    _description = u'Academy competency unit'

    _rec_name = 'name'
    _order = 'professional_qualification_id ASC, sequence ASC, competency_name ASC'

    _inherits = {'academy.training.module': 'training_module_id'}

    competency_name = fields.Char(
        string='Competency name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
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
        required=False,
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


    # -------------------------- OVERLOADED METHODS ---------------------------

    # @api.one
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
