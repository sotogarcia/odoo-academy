# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval

from logging import getLogger

_logger = getLogger(__name__)


class CivilServiceTrackerPublicAdministration(models.Model):

    _name = 'civil.service.tracker.public.administration'
    _description = u'Civil service tracker public administration'

    _table = 'cst_public_administration'

    _inherit = ['civil.service.tracker.institution.mixin']

    _rec_name = 'name'
    _order = 'name ASC'

    administration_type_id = fields.Many2one(
        comodel_name='civil.service.tracker.administration.type',
        string='Administration type',
        required=True,
        index=True,
        ondelete='cascade',
        help="Specific classification of the administration (e.g. AGE, Xunta, Concello).",
    )

    administration_scope_id = fields.Many2one(
        related='administration_type_id.administration_scope_id',
        string='Administration scope',
        store=True,
        readonly=True,
        help="Scope of the administration (e.g. state, regional, local).",
    )

    region_required = fields.Boolean(
        related='administration_scope_id.region_required',
        string='Region required',
        store=True,
        readonly=True,
        help="Whether administrative region must be set for this scope.",
    )

    position_label = fields.Char(
        string='Position label',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=("Label to display instead of the generic field name \'Service "
              "position', such as 'Corps', 'Category', 'Professional group', "
              "etc."),
        translate=True
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

    last_offer_year = fields.Char(
        string='Offer year',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Year or years the offer refers to (e.g., 2023, 2024, ...).',
        translate=False,
        compute='_compute_last_offer_year',
        store=True
    )

    @api.depends('public_offer_ids.offer_year')
    def _compute_last_offer_year(self):
        if not self:
            return

        query = """
            SELECT 
                public_administration_id, 
                MAX(offer_year)
            FROM 
                cst_public_offer
            WHERE 
                active
                AND offer_year IS NOT NULL
                AND public_administration_id = ANY(%s)
            GROUP BY 
                public_administration_id
        """
        _logger.debug(f'_compute_last_offer_year: {query % self.ids}')
        self.env.cr.execute(query, (self.ids,))
        result = dict(self.env.cr.fetchall())
        _logger.debug(f'_compute_last_offer_year: {result}')

        for record in self:
            record.last_offer_year = result.get(record.id, None)
    
    employment_scheme_ids = fields.Many2many(
        string='Employment schemes',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='civil.service.tracker.employment.scheme',
        relation='cst_public_administration_employment_scheme_rel',
        column1='public_administration_id',
        column2='employment_scheme_id',
        domain=[],
        context={},
        limit=None
    )

    employment_scheme_count = fields.Integer(
        string='Employment scheme count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute='_compute_employment_scheme_count'
    )

    @api.depends('employment_scheme_ids')
    def _compute_employment_scheme_count(self):
        for record in self:
            record.employment_scheme_count = len(record.employment_scheme_ids)

    employment_group_ids = fields.Many2many(
        string='Employment groups',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='civil.service.tracker.employment.group',
        relation='cst_public_administration_employment_group_rel',
        column1='public_administration_id',
        column2='employment_group_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_employment_group_ids'
    )

    @api.depends('employment_scheme_ids.employment_group_ids')
    def _compute_employment_group_ids(self):
        for record in self:
            groups = record.mapped('employment_scheme_ids.employment_group_ids')
            record.employment_group_ids = groups

    service_position_ids = fields.One2many(
        string='Service position',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='civil.service.tracker.service.position',
        inverse_name='public_administration_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    # -------------------------------------------------------------------------
    # CONTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'unique_partner_public_admin',
            'UNIQUE(partner_id)',
            'A public administration is already linked to this partner.'
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
        context.update({'default_public_administration_id': self.id})
    
        domain = [('public_administration_id', '=', self.id)]
    
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

    def convert_to_issuing_authority(self, open_form=True):
        target_model = 'civil.service.tracker.issuing.authority'
        serialize_method = self._serialize_to_issuing_authority
        entity_set = self.convert_to(target_model, serialize_method)

        if open_form and entity_set and len(entity_set) == 1:
            act_xid = ('civil_service_tracker.'
                       'action_civil_services_issuing_authority_act_window')
            return self._serialize_form_action(act_xid, entity_set[0])

        return None

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def _serialize_to_issuing_authority(record):
        record.ensure_one()

        scope = record.administration_scope_id
        if not scope:
            message = _('The record must have an administration scope.')
            raise ValidationError(message)

        region = record.administrative_region_id
        region_required = record.region_required and region

        return {
            'partner_id': record.partner_id.id,
            'administration_scope_id': scope.id if scope else None, 
            'region_required': bool(region_required),
            'administrative_region_id': region.id if region else None
        }
