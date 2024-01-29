# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.osv.expression import OR, FALSE_DOMAIN

from logging import getLogger


_logger = getLogger(__name__)


WIZARD_STATES = [
    ('step1', 'Tests'),
    ('step2', 'Questions'),
]


# pylint: disable=locally-disabled, w0212
class ChangeOwnerWizard(models.TransientModel):
    """ This wizard allows managers to change questions and tests owner

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.change.owner.wizard'
    _description = u'Change owner wizard'

    _rec_name = 'id'
    _order = 'id ASC'

    _inherit = ['record.ownership.wizard']

    authorship = fields.Selection(
        string='Authorship',
        required=True,
        readonly=False,
        index=False,
        default='own',
        help=False,
        selection=[
            ('own', 'My own'),
            ('third', 'Third-party')
        ]
    )

    change_authorship = fields.Boolean(
        string='Change authorship',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to change authorship'
    )

    @api.depends('change_owner', 'owner_id', 'change_subrogate',
                 'subrogate_id', 'change_authorship', 'authorship')
    @api.depends_context('active_model', 'active_ids', 'active_id')
    def _compute_target_count(self):
        parent = super(ChangeOwnerWizard, self)
        parent._compute_target_count()

    def _change_was_indicated(self):
        parent = super(ChangeOwnerWizard, self)
        return parent._change_was_indicated() or self.change_authorship

    def _build_values(self):
        parent = super(ChangeOwnerWizard, self)
        values = parent._build_values()

        values['authorship'] = bool(self.authorship == 'own')

        return values

    def _build_authorship_domain(self):
        self.ensure_one()

        if self.change_authorship:
            authorship = bool(self.authorship == 'own')
            authorship_domain = [('authorship', '!=', authorship)]
        else:
            authorship_domain = FALSE_DOMAIN

        return authorship_domain

    def _build_property_domain(self):
        parent = super(ChangeOwnerWizard, self)
        property_domain = parent._build_property_domain()

        authorship_domain = self._build_authorship_domain()

        return OR([property_domain, authorship_domain])
