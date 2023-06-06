# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyCompetencyUnitTeacherRel(models.Model):
    """
    """

    _name = 'academy.competency.unit.teacher.rel'
    _description = u'Academy competency unit teacher rel'

    _rec_name = 'id'
    _order = 'training_action_id, competency_unit_id DESC, sequence ASC'

    teacher_id = fields.Many2one(
        string='Teacher',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Related teacher',
        comodel_name='academy.teacher',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Related training action',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Related competency unit',
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=True,
        default=0,
        help='Order of importance of the teacher in the competency unit'
    )

    email = fields.Char(
        string='Email',
        related='teacher_id.email'
    )

    phone = fields.Char(
        string='Phone',
        related='teacher_id.phone'
    )

    _sql_constraints = [
        (
            'UNIQUE_TEACHER_BY_COMPETENCY_UNIT',
            'UNIQUE(teacher_id, training_action_id, competency_unit_id)',
            _(u'The teacher had already been assigned to the competency unit')
        )
    ]
