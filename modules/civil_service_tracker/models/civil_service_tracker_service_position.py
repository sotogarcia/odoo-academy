# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerServicePosition(models.Model):

    _name = 'civil.service.tracker.service.position'
    _description = u'Civil service tracker service position'

    _table = 'cst_service_position'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name of the specific service position (e.g. Health Corps)',
        translate=True
    )

    short_name = fields.Char(
        string='Short name',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Commonly used or internal short name, e.g., "PSG".',
        translate=True,
        track_visibility='onchange',
        copy=False,
    )

    position_label = fields.Char(
        string='Position label',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=("Label to display instead of the generic field name \'Service "
              "position', such as 'Corps', 'Category', 'Professional group', "
              "etc."),
        translate=True
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

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Indicates whether this administrative scope is currently active'
    )

    public_administration_id = fields.Many2one(
        string='Administration',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Public administration with its own position structure',
        comodel_name='civil.service.tracker.public.administration',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('public_administration_id')
    def _onchange_public_administration_id(self):
        for record in self:
            record.employment_group_id = None
            if not record.position_label:
                label = record.public_administration_id.position_label
                record.position_label = label
        
        group_set = record.public_administration_id.employment_group_ids

        return {
            'domain': {
                'employment_group_id': [('id', 'in', group_set.ids)]
            }
        }

    employment_group_id = fields.Many2one(
        string='Group',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Employment group (e.g., C1, C2, Group A)',
        comodel_name='civil.service.tracker.employment.group',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    contract_type_id = fields.Many2one(
        string='Contract type',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Type of employment contract (e.g. civil servant, labor staff)',
        comodel_name='civil.service.tracker.contract.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )
    
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
        """
        Overrides the default name_search to allow matching by both 'name'
        and 'short_name' fields in global search.
        """
        args = args or []

        domain = ['|',
                  ('name', operator, name),
                  ('short_name', operator, name)]

        return self.search(domain + args, limit=limit).name_get()
        
    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value

        if value is None:
            return False

        return str(value).strip().lower() in ('1', 'true', 'yes', 'on')
