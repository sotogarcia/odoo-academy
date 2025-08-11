# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.osv.expression import TRUE_DOMAIN
from odoo.tools import safe_eval
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerRelatedPartnerWizard(models.TransientModel):
    """
    Transient model (wizard) that allows users to locate and review all
    partners (res.partner) related to the civil service selection process
    management system.

    This includes entities such as public administrations, issuing authorities,
    delegated authorities, and organizations that have issued specific events
    within selection processes. The wizard provides filtering options and
    displays results using the standard Contacts view.
    """

    _name = 'civil.service.tracker.related.partner.wizard'
    _description = u'Civil service tracker related partner wizard'

    _table = 'cst_related_partner_wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    # -------------------------------------------------------------------------
    # WIARD FIELDS
    # -------------------------------------------------------------------------

    public_administrations = fields.Boolean(
        string='Public administrations',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Include partners linked to public administrations '
               'participating in selection processes.')
    )

    issuing_authorities = fields.Boolean(
        string='Issuing authorities',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Include partners acting as official authorities responsible '
              'for issuing public offers.')
    )

    delegated_authorities = fields.Boolean(
        string='Delegated authorities',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=('Include partners designated to manage public offers on behalf '
              'of the issuing authority.')
    )

    process_event_issuers = fields.Boolean(
        string='Authorities that issued events',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=('Include partners registered as issuers of events in selection '
              'processes.')

    )

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    @api.model
    def _search_for_service_partners(self):
        Partner = self.env['res.partner']
        partner_set = Partner.browse()

        target_partner_ids = set()

        if self.public_administrations:
            Admin = self.env['civil.service.tracker.public.administration']
            admin_rows = Admin.search_read(TRUE_DOMAIN, ['partner_id'])
            admin_partner_ids = [
                admin['partner_id'][0] for admin in admin_rows 
                if admin['partner_id']
            ]
            target_partner_ids.update(admin_partner_ids)

        if self.issuing_authorities:
            Authority = self.env['civil.service.tracker.issuing.authority']
            authority_rows = Authority.search_read(TRUE_DOMAIN, ['partner_id'])
            authority_partner_ids = [
                authority['partner_id'][0] for authority in authority_rows 
                if authority['partner_id']
            ]
            target_partner_ids.update(authority_partner_ids)

        if self.delegated_authorities:
            Offer = self.env['civil.service.tracker.public.offer']
            offer_rows = Offer.search_read(
                TRUE_DOMAIN, ['delegated_authority_id']
            )
            offer_partner_ids = [
                offer['delegated_authority_id'][0] 
                for offer in offer_rows 
                if offer['delegated_authority_id']
            ]
            target_partner_ids.update(offer_partner_ids)

        if self.process_event_issuers:
            Event = self.env['civil.service.tracker.process.event']
            event_rows = Event.search_read(TRUE_DOMAIN, ['issuer_partner_id'])
            event_partner_ids = [
                event['issuer_partner_id'][0] 
                for event in event_rows 
                if event['issuer_partner_id']
            ]
            target_partner_ids.update(event_partner_ids)

        if target_partner_ids:
            target_partner_ids = [pid for pid in target_partner_ids if pid]
            partner_obj = self.env['res.partner']
            partner_set = partner_obj.browse(target_partner_ids)

        return partner_set

    def _show_partners(self, partner_set):
        action_xid = 'contacts.action_contacts'
        act_wnd = self.env.ref(action_xid, raise_if_not_found=False)
        if not act_wnd:
            message = _('Contacts module has not been installed or the action '
                        'to open partner views has been deleted.')
            raise UserError(message)
    
        context = self.env.context.copy()
        if act_wnd.context:
            context.update(safe_eval(act_wnd.context))
        context.update({
            'showing_only_civil_service_partners': True,
            'default_order': 'name asc'
        })
    
        domain = [('id', 'in', partner_set.ids)]
    
        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': act_wnd.res_model,
            'target': 'main',
            'name': act_wnd.name,
            'view_mode': act_wnd.view_mode,
            'domain': domain,
            'context': context,
            'search_view_id': act_wnd.search_view_id.id,
            'help': act_wnd.help
        }
    
        return serialized
    
    def _notify_no_partners(self):
        message = _('There are no partners linked to civil service records '
                    'matching the selected types.')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('No partners'),
                'message': message,
                'sticky': False,
                'type': 'warning',
            }
        }

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def do_action(self):
        """
        Executes the wizard logic to retrieve and display related partners.

        Based on the user's selections, this method gathers all associated 
        partners from the civil service tracking system and opens a filtered 
        Contacts view with the results. If no related partners are found, 
        a warning notification is shown instead.
        """

        self.ensure_one()

        partner_set = self._search_for_service_partners()
        if not partner_set:
            result = self._notify_no_partners()
        else:
            result = self._show_partners(partner_set)

        return result
