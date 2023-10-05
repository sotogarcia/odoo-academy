# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class CalendarEvent(models.Model):
    """ Extends calendar.model_calendar_event
    """

    _name = 'calendar.event'
    _inherit = ['calendar.event']

    session_id = fields.Many2one(
        string='Session',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related training or non training session',
        comodel_name='academy.training.session',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    _sql_constraints = [
        (
            'unique_session_by_user',
            'UNIQUE(session_id, user_id)',
            _('Session had already been transferred to the user\'s calendar')
        )
    ]
