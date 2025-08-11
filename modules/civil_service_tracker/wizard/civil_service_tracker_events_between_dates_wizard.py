# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN
from odoo.exceptions import ValidationError, UserError

from logging import getLogger
from datetime import datetime, timedelta, time
from email_validator import validate_email, EmailNotValidError
from collections import defaultdict
from urllib.parse import urljoin
from pytz import all_timezones, timezone, utc


_logger = getLogger(__name__)


class CivilServiceTrackerEventsBetweenDatesWizard(models.TransientModel):

    _name = 'civil.service.tracker.events.between.dates.wizard'
    _description = u'Civil service tracker events between dates wizard'

    _table = 'cst_events_between_dates_wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    state = fields.Selection(
        string='Wizard step',
        required=True,
        readonly=False,
        index=False,
        default='step1',
        help=('Internal step of the wizard. Controls which inputs are shown '
              'at each stage.'),
        selection=[
            ('step1', 'Step 1'), 
            ('step2', 'Step 2'),
            ('step3', 'Step 3')
        ]
    )

    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'step2':
            self.process_event_ids = self._search_target_events()
        elif self.state == 'step3':
            if not self.process_event_ids:
                self.state = 'step2'
            self.subject = self.compute_subject()
            self.recipient_ids |= self._search_target_recipients()

    date_type = fields.Selection(
        string='Date type',
        required=True,
        readonly=False,
        index=False,
        default='event_date',
        help=('Determines which date field is used to filter events: event '
              'date, creation date, or last update date.'),
        selection=[
            ('event_date', 'Event date'), 
            ('create_date', 'Create date'), 
            ('write_date', 'Last update')
        ]
    )

    tz_name = fields.Selection(
        string='Timezone',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._context.get('tz'),
        help='Time zone to use for date/time calculations.',
        selection='_tz_get'
    )

    def _tz_get(self):
        tzs = [
            (tz, tz) for tz in sorted(
                all_timezones, 
                key=lambda tz: tz if not tz.startswith('Etc/') else '_'
            )
        ]
        
        return tzs

    date_start = fields.Datetime(
        string='Date start',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_date_start(),
        help='Start of the period for which to collect and notify events.'
    )

    date_start_tz = fields.Datetime(
        string='Localized start date',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=('start of the period to collect and notify events '
              '(in the selected time zone).'),
        compute='_compute_date_start_tz'
    )

    @api.depends('date_start', 'tz_name')
    def _compute_date_start_tz(self):
        for record in self:
            if record.date_start:
                dt = record.date_start
                tz_name = record.tz_name or 'UTC'
                record.date_start_tz = record.localize_datetime(dt, tz_name)
            else:
                record.date_start_tz = False

    def default_date_start(self):
        today = fields.Date.context_today(self)

        tz_name = self.env.user.tz or 'UTC'
        user_tz = timezone(tz_name)

        utc_midnight = datetime.combine(today, time.min)
        local_midnight = user_tz.localize(utc_midnight)
        utc_midnight_naive = local_midnight.astimezone(utc)

        return utc_midnight_naive.replace(tzinfo=None)

    date_stop = fields.Datetime(
        string='Date stop',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_date_stop(),
        help='End of the period for which to collect and notify events.'
    )

    date_stop_tz = fields.Datetime(
        string='Localized end date',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=('End of the period to collect and notify events '
              '(in the selected time zone).'),

        compute='_compute_date_stop_tz'
    )

    @api.depends('date_stop', 'tz_name')
    def _compute_date_stop_tz(self):
        for record in self:
            if record.date_stop:
                dt = record.date_stop
                tz_name = record.tz_name or 'UTC'
                record.date_stop_tz = record.localize_datetime(dt, tz_name)
            else:
                record.date_stop_tz = False

    def default_date_stop(self):
        tomorrow = fields.Date.context_today(self) + timedelta(days=1)
        
        tz_name = self.env.user.tz or 'UTC'
        user_tz = timezone(tz_name)
        
        utc_midnight = datetime.combine(tomorrow, time.min)
        local_midnight = user_tz.localize(utc_midnight)
        utc_midnight_naive = local_midnight.astimezone(utc)

        return utc_midnight_naive.replace(tzinfo=None)

    sender_type = fields.Selection(
        string='Sender type',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_sender_type(),
        help=('Defines the type of sender: a company, a specific user, or a '
              'custom email address.'),
        selection=[
            ('company_id', 'Company'), 
            ('sender_id', 'User'),
            ('sender_email', 'Other')
        ]
    )

    def default_sender_type(self):
        can_choose_sender = self._can_choose_sender(self.env.user)
        return 'company_id' if can_choose_sender else 'sender_id'

    @api.onchange('sender_type')
    def _onchange_sender_type(self):
        if self.sender_type == 'company_id':
            if not self.company_id:
                self.company_id = self.default_company_id()

            self.sender_email = self.company_id.email

        elif self.sender_type == 'sender_id':
            if not self.sender_id:
                self.sender_id = self.default_sender_id()

            self.sender_email = self.sender_id.email

        elif self.sender_type == 'sender_email':
            self.sender_email = self.default_sender_email()

    company_id = fields.Many2one(
        string='Company',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_company_id(),
        help='Company context used for template rendering and access rights.',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def default_company_id(self):
        company = None
        
        allowed_company_ids = self.env.context.get('allowed_company_ids', [])
        if allowed_company_ids:
            company_obj = self.env['res.company']
            company = company_obj.browse(allowed_company_ids[0])
        else:
            user = self.env.user or self.env.ref('base.user_root')
            company = user.company_id

        if not company:
            raise UserError('There is not a default company to use')

        return company

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.sender_id = self.env.user

        self._onchange_sender_type()

        if self.company_id:
            user_domain = [('company_ids', '=', self.company_id.id)]
        else:
            user_domain  = FALSE_DOMAIN

        return {
            'domain': {
                'sender_id': user_domain 
            }
        }

    sender_id = fields.Many2one(
        string='User',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_sender_id(),
        help='User responsible for sending the notification.', 
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def default_sender_id(self):
        return self.env.user or self.env.ref('base.user_root')

    @api.onchange('sender_id')
    def _onchange_sender_id(self):
        if self.sender_type == 'sender_id':
            self._onchange_sender_type()

    sender_email = fields.Char(
        string='Sender email',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_sender_email(),
        help='Email address used as the sender in the outgoing notification.',
        translate=False
    )

    def default_sender_email(self):
        if self.sender_type == 'company_id':
            company = self.company_id or self.default_company_id()
            return self.company_id.email

        if self.sender_type == 'sender_id':
            user = self.sender_id or self.default_sender_id()
            return user.email

        return self.default_reply_to_email()

    reply_to = fields.Boolean(
        string='Add reply-to',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Enable this option to add a reply-to email header.'
    )

    reply_to_email = fields.Char(
        string='Reply to email',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_reply_to_email(),
        help=('Email address used for replies. Defaults to a company-specific '
              'no-reply address.'),
        translate=False
    )

    def default_reply_to_email(self):
        Config = self.env['ir.config_parameter'].sudo()
        no_reply = Config.get_param('mail.default.from', 'no-reply')
        
        company = self.company_id or self.env.user.company_id
        if not company:
            domain = []
            Company = self.env['res.company']
            company = Company.search(domain, order='id ASC', limit=1)

        if company:
            email_parts = (company.email or '').split('@')
            if len(email_parts) == 2:
                email = f'{no_reply}@{email_parts[1]}'
        else:
            email = f'noreply@domain.local'

        return email

    subject = fields.Char(
        string='Subject',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Subject line of the message to be sent.',
        translate=True
    )

    can_choose_sender = fields.Boolean(
        string='Can choose sender',
        required=False,
        readonly=True,
        index=False,
        default=lambda self: self.default_can_choose_sender(),
        help=('Indicates whether the current user can choose another user '
              'as sender.')
    )

    def default_can_choose_sender(self):
        return self._can_choose_sender(self.env.user)

    process_event_ids = fields.Many2many(
        string='Process events',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=('List of events that occurred between the selected dates and '
              'will be included in the email.'),
        comodel_name='civil.service.tracker.process.event',
        relation='cst_events_between_dates_wizard_process_event_rel',
        column1='wizard_id',
        column2='process_event_id',
        domain=[],
        context={},
        limit=None
    )

    partner_category_ids = fields.Many2many(
        string='Partner categories',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner.category',
        relation='cst_events_between_dates_wizard_res_partner_category_rel',
        column1='wizard_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None
    )

    recipient_ids = fields.Many2many(
        string='Recipients',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        relation='cst_events_between_dates_wizard_res_partner_rel',
        column1='wizard_id',
        column2='partner_id',
        domain=[],
        context={},
        limit=None
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    @api.constrains('process_event_ids')
    def _check_process_event_ids(self):
        message = _("You must select at least one process event.")
        for record in self:
            if not record.process_event_ids:
                raise ValidationError(message)

    @api.constrains('recipient_ids')
    def _check_recipient_ids(self):
        message = _("You must select at least one recipient.")
        for record in self:
            if not record.recipient_ids:
                raise ValidationError(message)

    @api.constrains('sender_email', 'reply_to_email')
    def _check_email_fields(self):
        check_address = self.check_email_address

        for record in self:
            check_address(record.sender_email, raise_exception=True)
            if record.reply_to:
                check_address(record.reply_to_email, raise_exception=True)

    _sql_constraints = [
        (
            'check_date_range',
            'CHECK(date_start <= date_stop)',
            'The start date must be earlier than or equal to the end date.'
        ),
        (
            'check_subject_min_length',
            "CHECK (char_length(subject) >= 3)",
            "The subject must contain at least 3 characters."
        ),
    ]

    # -------------------------------------------------------------------------
    # OVERRIDING METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def check_email_address(email, raise_exception=True):
        try:
            validate_email(email or '', check_deliverability=False)
            return True
        except EmailNotValidError as e:
            if raise_exception:
                message = _("Invalid email format '%s'. %s")
                raise ValidationError(message % (email, str(e)))
            return False

    @api.model
    def create(self, vals):
        self._check_sender_access(vals.get('sender_id'))
        return super().create(vals)

    def write(self, vals):
        if 'sender_id' in vals:
            self._check_sender_access(vals['sender_id'])
        return super().write(vals)

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    def compute_subject(self):
        self.ensure_one()

        msg_all_day = _('Selection process events on {}')
        msg_day_range = _('Selection process events between {} and {} on {}')
        msg_date_range = _('Selection process events between {} and {}')
        msg_multi_day = _('Selection process events from {} on {} to {} on {}')

        date_start = self.date_start_tz
        date_stop = self.date_stop_tz

        if self._is_all_day(date_start, date_stop):
            subject = msg_all_day.format(date_start.strftime('%x'))
        elif self._is_day_range(date_start, date_stop):
            subject = msg_day_range.format(
                date_start.strftime('%X'),
                date_stop.strftime('%X'),
                date_start.strftime('%x')
            )
        elif self._is_date_range(date_start, date_stop):
            subject = msg_date_range.format(
                date_start.strftime('%x'),
                (date_stop - timedelta(days=1)).strftime('%x')
            )
        else:
            subject = msg_multi_day.format(
                date_start.strftime('%X'),
                date_start.strftime('%x'),
                date_stop.strftime('%X'),
                date_stop.strftime('%x')
            )

        return subject

    @classmethod
    def _is_all_day(cls, date_start, date_stop):
        return (
            date_start.time() == time.min and
            date_stop.time() == time.min and
            (date_stop - date_start) == timedelta(days=1)
        )

    @staticmethod
    def _is_day_range(date_start, date_stop):
        return date_start.date() == date_stop.date()

    @staticmethod
    def _is_date_range(date_start, date_stop):
        return (
            date_start.time() == time.min and
            date_stop.time() == time.min and
            (date_stop - date_start) >= timedelta(days=1)
        )

    @api.model
    def _can_choose_sender(self, user):
        return self.env.user.has_group(
            'civil_service_tracker.group_civil_service_tracker_admin'
        )

    @staticmethod
    def localize_datetime(dt, tz_name):
        try:
            local_tz = timezone(tz_name)
            utc_dt = dt.replace(tzinfo=utc)
            local_dt = utc_dt.astimezone(local_tz).replace(tzinfo=None)
            return local_dt
        except Exception as e:
            _logger.warning(
                "Timezone conversion failed for tz '%s': %s", tz_name, e
            )
            return dt  # Devuelve original como fallback

    def _search_target_events(self):
        self.ensure_one()

        field_name = self.date_type
        event_domain = [
            (field_name, '>=', self.date_start),
            (field_name, '<', self.date_stop),
        ]
        Event = self.env['civil.service.tracker.process.event']
        event_set = Event.search(event_domain)
        
        return event_set

    def _search_target_recipients(self):
        self.ensure_one()

        Partner = self.env['res.partner']
        partner_set = Partner.browse()

        if self.partner_category_ids:
            category_ids = self.partner_category_ids.ids
            partner_domain = [('category_id', 'in', category_ids)]
            partner_obj = self.env['res.partner']
            partner_set = partner_obj.search(partner_domain, order="name")
            
        return partner_set | self.sender_id.partner_id

    def _check_sender_access(self, sender_id):
        if not sender_id:
            return

        if sender_id != self.env.uid:
            admin_group = \
                'civil_service_tracker.group_civil_service_tracker_admin'
            if not self.env.user.has_group(admin_group):
                raise AccessError(
                    _('Only administrators can assign another user as sender.')
                )

    def _group_events_by_admin_and_process(self):
        grouped = defaultdict(lambda: defaultdict(list))
        for event in self.process_event_ids:
            process = event.selection_process_id
            administration = process.public_administration_id

            grouped[administration][process].append(event)

        return grouped

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def get_email_from(self, raise_if_not_email=True):
        name, email = False, False

        if self.sender_type == 'company_id':
            name = self.company_id.name
            email = self.company_id.email
        elif self.sender_type == 'sender_id':
            name = self.sender_id.name
            email = self.sender_id.email
        elif self.sender_type == 'sender_email':
            name = self.sender_id.name
            email = self.sender_email
        else:
            raise UserError(_('Unexpected type of sender.'))

        if raise_if_not_email and not email:
            raise ValidationError(_('Empty email address'))

        return f'{name} <{email}>' if name else email

    def get_reply_to(self):
        reply_to_email = self.reply_to and self.reply_to_email
        return reply_to_email or self.get_email_from()

    # -------------------------------------------------------------------------
    # WIZARD MAIN LOGIC
    # -------------------------------------------------------------------------

    def perform_action(self):
        self.ensure_one()

        template = self.env.ref(
            'civil_service_tracker.'
            'mail_template_civil_service_tracker_events_between_dates_wizard'
        )

        if not self.recipient_ids:
            raise UserError(_("You must select at least one recipient."))

        grouped = self._group_events_by_admin_and_process()
        
        Config = self.env['ir.config_parameter'].sudo()
        base_url = Config.get_param('web.base.url')

        for recipient in self.recipient_ids:
            if not recipient.email:
                continue  # Skip recipients with no email

            context = self.env.context.copy()
            context.update(
                grouped_events=grouped, 
                recipient=recipient, 
                base_url=base_url
            )

            template.with_context(context).send_mail(
                self.id,
                force_send=True,
                email_values={'email_to': recipient.email}
            )

        return {'type': 'ir.actions.act_window_close'}
