# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceRecruitmentProcess(models.Model):
    """ All information about the public examination process
    """

    _inherit = ['civil.service.recruitment.process']

    training_action_ids = fields.Many2many(
        string='Training action',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        relation='academy_training_action_public_tendering_process_rel',
        column1='public_tendering_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None
    )

    training_action_id = fields.Many2one(
        string='Default training action',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the default training action for public tendering',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        tracking=True
    )

    @api.constrains('training_action_id', 'training_action_ids')
    def _check_training_action(self):
        message = _('The default training action should be in the list')

        for record in self:

            default = record.training_action_id
            available = record.training_action_ids

            if default and default not in available:
                raise ValidationError(message)
