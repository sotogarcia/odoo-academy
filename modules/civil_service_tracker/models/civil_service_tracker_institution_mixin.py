# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval

from logging import getLogger
from uuid import uuid4


_logger = getLogger(__name__)


class CivilServiceTrackerInstitutionMixin(models.AbstractModel):

    _name = 'civil.service.tracker.institution.mixin'
    _description = u'Civil service tracker institution mixin'

    _table = 'cst_institution_mixin'

    _inherit = ['mail.thread']

    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        string='Partner',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        copy=False
    )

    creation_mode = fields.Selection(
        string='Creation mode',
        required=True,
        readonly=False,
        index=False,
        default='new',
        help=('Choose whether to create a new administration from scratch or '
              'link it to an existing partner.'),
        selection=[
            ('new', 'Create new from scratch'),
            ('link', 'Link to an existing partner'),
        ]
    )

    short_name = fields.Char(
        string='Short name',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Commonly used or internal abbreviation, e.g., "AGE".',
        translate=True,
        copy=False
    )
    
    token = fields.Char(
        string='Token',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: str(uuid4()),
        help='Unique token used to identify this record.',
        translate=False,
        copy=False,
        track_visibility='always'
    )

    administrative_region_id = fields.Many2one(
        string='Administrative region',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='civil.service.tracker.administrative.region',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Optional description providing additional context',
        translate=True
    )
 
    # -------------------------------------------------------------------------
    # OVERWRITTEN METHODS
    # -------------------------------------------------------------------------

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)
        
        defaults['company_type'] = 'company'
        defaults['is_company'] = True

        company = self.env.user.company_id
        if company and company.country_id:
            defaults['country_id'] = company.country_id.id

        return defaults

    def name_get(self):
        config = self.env['ir.config_parameter'].sudo()
        param_name = 'civil_service_tracker.display_process_short_name'

        raw_value = config.get_param(param_name)
        use_short = self._to_bool(raw_value)

        result = []
        for record in self:
            if use_short and record.short_name:
                name = record.short_name
            else:
                name = record.name
            result.append((record.id, name))

        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Allows matching by both 'name' and 'short_name' when performing
        global search."""
        
        args = args or []

        domain = ['|',
                  ('name', operator, name),
                  ('short_name', operator, name)]

        return self.search(domain + args, limit=limit).name_get()

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------
 
    def view_partners(self):
        action_xid = 'contacts.action_contacts'
        act_wnd = self.env.ref(action_xid)
    
        context = self.env.context.copy()
        if act_wnd.context:
            context.update(safe_eval(act_wnd.context))

        domain = [('id', 'in', self.mapped('partner_id').ids)]
    
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

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------
    
    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value

        if value is None:
            return False

        return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

    def convert_to(self, model, serialize_method):
        Entity = self.env[model]
        entity_set = Entity.browse()

        for record in self:
            if isinstance(record.id, models.NewId) or not record.partner_id:
                continue

            # Check if target entity already exists
            partner_id = record.partner_id.id
            domain = [('partner_id', '=', partner_id)]
            entity = Entity.search(domain, limit=1)

            if entity: # If exists add it to the result set
                entity_set |= entity
            
            else:  # If not exists create it and add it to the result set
                values = serialize_method(record)
                entity_set |= Entity.create(values)

        return entity_set

    @api.model
    def _serialize_form_action(self, act_wnd_xid, entity):
        entity.ensure_one()

        act_wnd = self.env.ref(act_wnd_xid, raise_if_not_found=False)
        if not act_wnd:
            raise ValueError(f'Action window {act_wnd_xid} not found.')

        view_mode = act_wnd.view_mode
        if isinstance(view_mode, str):
            view_mode = view_mode.split(',')
        view_mode = [mode for mode in view_mode if mode != 'form']
        view_mode.insert(0, 'form')

        context = safe_eval(act_wnd.context) if act_wnd.context else {}
        domain = safe_eval(act_wnd.domain) if act_wnd.domain else []

        return {
            'type': 'ir.actions.act_window',
            'res_model': act_wnd.res_model,
            'target': 'new',
            'name': act_wnd.name,
            'view_mode': ','.join(view_mode),
            'domain': domain,
            'context': context,
            'search_view_id': act_wnd.search_view_id.id,
            'help': act_wnd.help,
            'res_id': entity.id
        }

