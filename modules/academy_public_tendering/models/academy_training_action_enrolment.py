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

    def name_get(self):
        """ Computes special name joining student namen and item name.

        By order, ``item`` name can be the module name, the process name or
        the action name.

        Returns:
            list -- list of tuples [(id, name)]
        """

        result = []

        for record in self:
            student = record.student_id.name
            if len(record.training_module_ids) == 1:
                item = record.training_module_ids.name
            else:
                if(record.public_tendering_process_id):
                    item = record.public_tendering_process_id.name
                else:
                    item = record.training_action_id.name

            if student and item:
                name = '{} - {}'.format(item, student)
            else:
                name = _('New training action enrolment')

            result.append((record.id, name))

        return result
