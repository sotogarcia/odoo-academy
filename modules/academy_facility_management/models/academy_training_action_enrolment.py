# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionEnrolment(models.Model):
    """ Display facility and complex in enrolments
    """

    _name = 'academy.training.action.enrolment'
    _inherit = 'academy.training.action.enrolment'

    primary_facility_id = fields.Many2one(
        string='Primary facility',
        related='training_action_id.primary_facility_id'
    )

    primary_complex_id = fields.Many2one(
        string='Primary complex',
        related='training_action_id.primary_complex_id'
    )
