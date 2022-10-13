# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.action.enrolment Odoo model which stores
all training action attributes and behavior.

"""

from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingActionEnrolment(models.Model):
    """ This model stores attributes and behavior relative to the
    enrollment of students in academy training actions
    """

    _inherit = 'academy.training.action.enrolment'

    public_tendering_process_id = fields.Many2one(
        string='Public tendering',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose public tendering in which the student will be enrolled',
        comodel_name='academy.public.tendering.process',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    # def name_get(self):
    #     """ Uses public tendering process name in display name
    #     """
    #     result = []

    #     for record in self:
    #         if not record.public_tendering_process_id:
    #             _super = super(AcademyTrainingActionEnrolment, record)
    #             name = _super.name_get()[0][1]
    #         else:
    #             student = record.student_id.name
    #             process = record.public_tendering_process_id.name

    #             name = '{} - {}'.format(process, student)

    #         result.append((record.id, name))

    #     return result
