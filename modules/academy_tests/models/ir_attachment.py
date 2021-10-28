# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger


_logger = getLogger(__name__)


class IrAttachment(models.Model):
    """ Appends owner_id field. This do not inherit from abstract model
    'academy.abstract.owner' because field value cant not be required or
    Odoo breaks with some other model operations.
    """

    _name = 'ir.attachment'
    _inherit = ['ir.attachment']

    owner_id = fields.Many2one(
        string='Owner',
        required=False,
        readonly=False,
        index=True,
        default=lambda self: self._default_owner_id(),
        help='Current owner',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    def _default_owner_id(self):
        """ Compute the default owner for new questions; this will be
        the current user or the root user.
        @note: root user will be used only for background actions.
        """

        return self.env.context.get('uid', 1)
