# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module contains the professional.qualification.unit Odoo model which stores
all professional.qualification attributes and behavior.

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api


# pylint: disable=locally-disabled, c0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalQualification(models.Model):
    """ Set of qualifications according to criteria of affinity of professional
    competence..

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.professional.qualification'
    _description = u'Academy professional qualification'

    _inherit = ['image.mixin']

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=100,
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

    competency_unit_ids = fields.One2many(
        string='Academy competency units',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related competency units',
        comodel_name='academy.competency.unit',
        inverse_name='professional_qualification_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
    )


    professional_family_id = fields.Many2one(
        string='Professional family',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related professional family',
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
        help='Choose related professional area',
        comodel_name='academy.professional.area',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    qualification_code = fields.Char(
        string='Internal code',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Enter new internal code',
        size=30,
        translate=True,
    )

    qualification_level_id = fields.Many2one(
        string='Qualification level',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related qualification level',
        comodel_name='academy.qualification.level',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )


    # --------------------------- MANAGEMENT FIELDS ---------------------------

    # pylint: disable=locally-disabled, W0212
    competency_unit_count = fields.Integer(
        string='Competency units',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of competency units related with this professional qualification',
        compute=lambda self: self._compute_competency_unit_count()
    )


    # @api.multi
    @api.depends('competency_unit_ids')
    def _compute_competency_unit_count(self):
        for record in self:
            record.competency_unit_count = len(record.competency_unit_ids)
