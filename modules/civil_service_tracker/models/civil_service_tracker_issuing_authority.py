# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.exceptions import ValidationError

from logging import getLogger
from uuid import uuid4


_logger = getLogger(__name__)


class CivilServiceTrackerIssuingAuthority(models.Model):

    _name = 'civil.service.tracker.issuing.authority'
    _description = u'Civil service tracker issuing authority'

    _table = 'cst_issuing_authority'

    _inherit = ['civil.service.tracker.institution.mixin']

    _rec_name = 'name'
    _order = 'name ASC'

    administration_scope_id = fields.Many2one(
        string='Administration scope',
        required=True,
        index=True,
        ondelete='cascade',
        readonly=False,
        default=None,
        help="Scope of the administration (e.g. state, regional, local)",
        comodel_name='civil.service.tracker.administration.scope',
        domain=[],
        context={},
        auto_join=False,
    )

    region_required = fields.Boolean(
        related='administration_scope_id.region_required',
        string='Region required',
        store=True,
        readonly=True,
        help="Whether administrative region must be set for this scope.",
    )

    public_offer_ids = fields.One2many(
        string='Offers',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='civil.service.tracker.public.offer',
        inverse_name='public_administration_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    public_offer_count = fields.Integer(
        string='Offer count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute='_compute_public_offer_count'
    )
    
    @api.depends('public_offer_ids')
    def _compute_public_offer_count(self):
        for record in self:
            record.public_offer_count = len(record.public_offer_ids)
    
    # -------------------------------------------------------------------------
    # CONTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'unique_partner_issuing_authority',
            'UNIQUE(partner_id)',
            'An issuing authority is already linked to this partner.'
        ),
    ]

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def view_public_offers(self):
        self.ensure_one()
    
        action_xid = ('civil_service_tracker.'
                      'action_civil_services_public_offer_act_window')
        act_wnd = self.env.ref(action_xid)
    
        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({'default_issuing_authority_id': self.id})
    
        domain = [('issuing_authority_id', '=', self.id)]
    
        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': act_wnd.res_model,
            'target': 'current',
            'name': act_wnd.name,
            'view_mode': act_wnd.view_mode,
            'domain': domain,
            'context': context,
            'search_view_id': act_wnd.search_view_id.id,
            'help': act_wnd.help
        }
    
        return serialized

    def convert_to_public_administration(self, open_form=True):
        target_model = 'civil.service.tracker.public.administration'
        serialize_method = self._serialize_to_public_administration
        entity_set = self.convert_to(target_model, serialize_method)

        if open_form and entity_set and len(entity_set) == 1:
            act_xid = (
                'civil_service_tracker.'
                'action_civil_services_public_administration_act_window'
            )
            return self._serialize_form_action(act_xid, entity_set[0])

        return None

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def _serialize_to_public_administration(record):
        record.ensure_one()

        scope = record.administration_scope_id
        if not scope:
            message = _('The record must have an administration scope.')
            raise ValidationError(message)

        region = record.administrative_region_id
        region_required = record.region_required and region

        administration_type_model = 'civil.service.tracker.administration.type'
        AdministrationType = record.env[administration_type_model]
        domain = [
            ('administration_scope_id', '=', scope.id),
            ('region_required', '=', region_required)
        ]
        administration_type = AdministrationType.search(domain, limit=1)
        if not administration_type:
            message = _(
                'No administration type matches the scope "%s" and the '
                'region requirement (%s).'
            ) % (scope.name, region_required)
            raise ValidationError(message)

        return {
            'partner_id': record.partner_id.id,
            'administration_type_id': administration_type.id, 
            'administrative_region_id': region.id if region else None
        }
