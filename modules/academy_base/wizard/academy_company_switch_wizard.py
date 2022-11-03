# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger


_logger = getLogger(__name__)


class AcademyCompanySwitchWizard(models.Model):
    """ Allows to switch company to the given records
    """

    _name = 'academy.company.switch.wizard'
    _description = u'Academy company switch'

    _rec_name = 'company_id'
    _order = 'company_id ASC'

    company_id = fields.Many2one(
        string='Company',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.env.company,
        help='The company selected records belongs to',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    record_count = fields.Integer(
        string='Record count',
        required=True,
        readonly=True,
        index=False,
        default=lambda self: self.default_record_count(),
        help='Number of records will be updated'
    )

    @api.model
    def default_record_count(self):
        return len(self._get_active_ids())

    @api.model
    def _get_active_ids(self):
        ctx = self.env.context

        active_id = ctx.get('active_id', False)

        return [active_id] if active_id else ctx.get('active_ids', [])

    @api.model
    def _get_active_model(self):
        return self.env.context.get('active_model', False)

    def switch_company(self, *args, **kwargs):
        model = self._get_active_model()
        active_ids = self._get_active_ids()

        domain = [('id', 'in', active_ids)]
        target_set = self.env[model].search(domain)

        target_set.company_id = self.company_id

        menu = self.env.ref('academy_base.menu_academy')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': menu.id},
        }
