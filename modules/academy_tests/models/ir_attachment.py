# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
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

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='List of the questions which are using this attachment',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_ir_attachment_rel',
        column1='attachment_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    def _default_owner_id(self):
        """ Compute the default owner for new questions; this will be
        the current user or the root user.
        @note: root user will be used only for background actions.
        """

        return self.env.context.get('uid', 1)

    @api.model_create_multi
    def create(self, vals_list):
        if self._has_been_called_from_question_import_wizard():
            self._required_question_import_wizard_values(vals_list)

        _super = super(IrAttachment, self)

        return _super.create(vals_list)

    def _has_been_called_from_question_import_wizard(self):
        return self.env.context.get('import_wizard', False)

    def _required_question_import_wizard_values(self, vals_list):
        for vals in vals_list:
            vals.update({
                'res_model': False,
                'res_field': False,
                'res_id': None,
                'public': True,
            })
