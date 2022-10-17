# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger
from odoo.addons.base_field_big_int.field import BigInt
from odoo.tools.translate import _

import re

_logger = getLogger(__name__)

OXID = 'academy_public_tendering.academy_public_tendering_event_type_job_offer'


class AcademyPublicTenderingRssItem(models.Model):
    """ Each one of the RSS entries
    """

    _name = 'academy.public.tendering.rss.item'
    _description = u'Academy public tendering RSS item'

    _rec_name = 'name'
    _order = 'safe_date DESC'

    name = fields.Char(
        string='Title',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='RSS item title',
        size=255,
        translate=False
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    link = fields.Char(
        string='Link',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='URL referenced in the RSS element',
        size=255,
        translate=False
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Additional information in the RSS element',
        translate=True
    )

    guid = fields.Char(
        string='GUID',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='GUID in the RSS element',
        size=255,
        translate=False
    )

    published = fields.Datetime(
        string='Published',
        required=False,
        readonly=True,
        index=False,
        default=fields.datetime.now(),
        help='Date and time it was published'
    )

    feed_id = fields.Many2one(
        string='RSS feed',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Parent RSS feed',
        comodel_name='academy.public.tendering.rss.feed',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    official = fields.Boolean(
        related='feed_id.official',
        readonly='True'
    )

    body = fields.Html(
        string='Body',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='HTML'
    )

    safe_date = fields.Datetime(
        string='Safe date',
        required=True,
        readonly=True,
        index=True,
        default=fields.datetime.now(),
        help='Publish date if available or create date'
    )

    event_ids = fields.One2many(
        string='Events',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='List all events related with this RSS item',
        comodel_name='academy.public.tendering.event',
        inverse_name='rss_item_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    event_count = fields.Integer(
        string='Event count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of events related with this RSS item',
        compute='_compute_event_count'
    )

    guid_hash = BigInt(
        string='Hash',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help='Hash to allow to check if item already exists'
    )

    _sql_constraints = [
        (
            'UNIQUE_GUID',
            'UNIQUE(guid)',
            _('RSS entry already exists')
        ),
        (
            'UNIQUE_GUID_HASH',
            'UNIQUE(guid_hash)',
            _('There is an RSS entry with the same hash')
        ),
    ]

    @api.depends('event_ids')
    def _compute_event_count(self):
        for record in self:
            record.event_count = len(record.event_ids)

    process_ids = fields.One2many(
        string='Process',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='List all processes related with this RSS item',
        comodel_name='academy.public.tendering.process',
        inverse_name='rss_item_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    process_count = fields.Integer(
        string='Process count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of processes related with this RSS item',
        compute='_compute_process_count'
    )

    @api.depends('process_ids')
    def _compute_process_count(self):
        for record in self:
            record.process_count = len(record.process_ids)

    offer_ids = fields.One2many(
        string='Offers',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='List all offers related with this RSS item',
        comodel_name='academy.public.tendering.public.offer',
        inverse_name='rss_item_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    offer_count = fields.Integer(
        string='Offer count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of offers related with this RSS item',
        compute='_compute_offer_count'
    )

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    @api.model
    def create(self, values):
        _super = super(AcademyPublicTenderingRssItem, self)

        if 'published' in values.keys() and values['published']:
            values['safe_date'] = values['published']

        if 'guid' in values.keys() and values['guid']:
            values['guid_hash'] = hash(values['guid'])

        return _super.create(values)

    def write(self, values):
        _super = super(AcademyPublicTenderingRssItem, self)

        if 'guid' in values.keys() and values['guid']:
            values['guid_hash'] = hash(values['guid'])

        return _super.write(values)

    def _try_to_find_admon(self):
        admon_obj = self.env['academy.public.tendering.public.administration']
        rows = admon_obj.search_read([], ['name'])

        admon_id, admon_name = None, None
        for row in rows:
            if re.search(row['name'], (self.name or ''), re.IGNORECASE) or \
               re.search(row['name'], (self.description or ''), re.IGNORECASE):
                admon_id, admon_name = row['id'], row['name']
                break

        return admon_id, admon_name

    def _try_to_find_offer(self):
        offer = self.env['academy.public.tendering.public.offer']

        admon_id, admon_name = self._try_to_find_admon()
        if admon_id:
            date = self.safe_date.strftime('%Y-%m-%d %H:%M:%S')
            domain = [
                ('public_administration_id', '=', admon_id),
                ('approval', '<=', date)
            ]
            offer = offer.search(domain, order="approval DESC", limit=1)

        return offer

    def _last_or_new_attachment(self):
        attach = self.env['ir.attachment']
        domain = [('type', '=', 'url'), ('url', '=ilike', self.link)]
        attach = attach.search(domain, order='write_date DESC', limit=1)

        if not attach:
            attach = self.sudo().env['ir.attachment']
            attach = attach.create({
                'name': self.feed_id.name,
                'type': 'url',
                'url': self.link,
            })

        return attach

    def new_offer(self):
        self.ensure_one()

        context = {
            'default_approval': self.safe_date,
        }

        admon_id, admon_name = self._try_to_find_admon()
        if admon_id and admon_name:
            context['default_public_administration_id'] = admon_id
            context['default_name'] = "{}, {}".format(
                admon_name, self.safe_date.year)

        if self.link:
            if self.official:
                context['default_official_journal_url'] = self.link
            else:
                context['default_bulletin_board_url'] = self.link

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.public.tendering.public.offer',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': context
        }

    def new_process(self):
        self.ensure_one()

        event = self.env.ref(OXID)
        ev_values = {
            'date': self.safe_date,
            'description': self.name,
            'event_type_id': event.id,
            'name': event.name,
            'rss_item_id': self.id,
        }
        context = {
            'default_public_process_event_ids': [(0, 0, ev_values)]
        }

        if self.link:
            if self.official:
                context['default_official_journal_url'] = self.link
            else:
                context['default_bulletin_board_url'] = self.link

            attach = self._last_or_new_attachment()
            ev_values['ir_atachment_id'] = attach.id

        offer = self._try_to_find_offer()
        if offer:
            context['default_public_offer_id'] = offer.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.public.tendering.process',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': context
        }

    def new_event(self):
        self.ensure_one()

        context = {
            'default_date': self.safe_date,
            'default_description': self.name,
            'default_rss_item_id': self.id
        }

        if self.link:
            attach = self._last_or_new_attachment()
            context['default_ir_atachment_id'] = attach.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.public.tendering.event',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': context
        }


