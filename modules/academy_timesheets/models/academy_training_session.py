# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools import safe_eval
from odoo.tools.translate import _
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import UserError, MissingError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

from datetime import timedelta, datetime, date, time
import pytz

from logging import getLogger


_logger = getLogger(__name__)

CHECK_TRAINING_TASK = '''
    CHECK(
        (kind <> \'teach\') OR
        (
            training_action_id IS NOT NULL
            AND competency_unit_id IS NOT NULL
            AND task_id IS NULL
        )
    )
'''

CHECK_NON_TRAINING_TASK = '''
    CHECK(
        (kind <> \'task\') OR
        (
            task_id IS NOT NULL
            AND training_action_id IS NULL
            AND competency_unit_id IS NULL
        )
    )
'''


class AcademyTrainingSession(models.Model):
    """ Temporarily delimited phase or act in which part of a training action
    takes place
    """

    _name = 'academy.training.session'
    _description = u'Academy training session'

    _inherit = ['mail.thread', 'ownership.mixin']

    _rec_name = 'id'
    _order = 'date_start ASC'

    _check_company_auto = True

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    state = fields.Selection(
        string='State',
        required=True,
        readonly=False,
        index=True,
        default='draft',
        help='Current session status',
        selection=[
            ('draft', 'Draft'),
            ('ready', 'Ready')
        ],
        groups="academy_base.academy_group_technical",
        track_visibility='onchange'
    )

    kind = fields.Selection(
        string='Type',
        required=True,
        readonly=False,
        index=True,
        default='teach',
        help=False,
        selection=[
            ('teach', 'Teaching task'),
            ('task', 'Non-teaching task')
        ]
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Related training action',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    company_id = fields.Many2one(
        string='Company',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help='The company this record belongs to',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_company_id',
        store=True
    )

    @api.depends('training_action_id', 'task_id')
    def _compute_company_id(self):

        for record in self:
            if record.training_action_id:
                record.company_id = record.training_action_id.company_id
            elif record.task_id:
                record.company_id = record.task_id.company_id
            else:
                record.company_id = None

    task_id = fields.Many2one(
        string='Non-teaching task',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Non-teaching task',
        comodel_name='academy.non.teaching.task',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        related='training_action_id.training_activity_id'
    )

    task_name = fields.Char(
        string='Training / Task',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help=False,
        size=1024,
        translate=True,
        compute='compute_task_name',
        store=True
    )

    @api.depends('training_action_id', 'task_id')
    def compute_task_name(self):
        for record in self:
            if record.training_action_id:
                record.task_name = record.training_action_id.action_name
            elif record.task_id:
                record.task_name = record.task_id.name
            else:
                record.task_name = _('New session')

    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):
        for record in self:
            record.competency_unit_id = None

            # Remove competency unit and restore it if it's valid for the new
            # set training action. It is necessary to change the competency
            # unit even if it is the same to trigger the corresponding onchange
            # if record.competency_unit_id:
            #     old_competency_unit = record.competency_unit_id

            #     record.competency_unit_id = None

            #     if self.training_action_id:
            #         lact = record.training_action_id.training_activity_id
            #         ract = old_competency_unit.training_activity_id

            #         if lact == ract:
            #             record.competency_unit_id = old_competency_unit

            link_ids = record.training_action_id.facility_link_ids
            if link_ids:
                o2m_ops = [(5, 0, 0)]
                for link in link_ids:
                    values = {
                        'facility_id': link.facility_id.id,
                        'sequence': link.sequence
                    }
                    o2m_op = (0, None, values)
                    o2m_ops.append(o2m_op)

                record.reservation_ids = o2m_ops

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Related competency unit',
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    @api.onchange('competency_unit_id')
    def _onchange_competency_unit_id(self):
        for record in self:
            unit = record.competency_unit_id
            action = record.training_action_id

            if unit and action:
                facility_set = unit.facility_assignment_ids.filtered(
                    lambda x: x.training_action_id.id == action.id)

                if facility_set:
                    record.reservation_ids = None

                    o2m_ops = [(5, 0, 0)]
                    for assign in facility_set:
                        values = {
                            'facility_id': assign.facility_id.id,
                            'sequence': assign.sequence
                        }
                        o2m_op = (0, None, values)
                        o2m_ops.append(o2m_op)

                    record.reservation_ids = o2m_ops

                teacher_set = unit.teacher_assignment_ids.filtered(
                    lambda x: x.training_action_id.id == action.id)

                if teacher_set:
                    record.teacher_assignment_ids = None

                    o2m_ops = [(5, 0, 0)]
                    for assign in teacher_set:
                        values = {
                            'teacher_id': assign.teacher_id.id,
                            'sequence': assign.sequence
                        }
                        o2m_op = (0, None, values)
                        o2m_ops.append(o2m_op)

                    record.teacher_assignment_ids = o2m_ops

    teacher_assignment_ids = fields.One2many(
        string='Teacher assignments',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_teacher_assignment_ids(),
        help=False,
        comodel_name='academy.training.session.teacher.rel',
        inverse_name='session_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        track_visibility='onchange',
        copy=False
    )

    def default_teacher_assignment_ids(self):
        result = None

        teacher_id = self.env.context.get('default_primary_teacher_id', None)
        if teacher_id and isinstance(teacher_id, int) and teacher_id > 0:

            teacher_obj = self.env['academy.teacher']
            teacher_set = teacher_obj.browse(teacher_id)

            if teacher_set:
                values = {'teacher_id': teacher_set.id, 'sequence': 1}
                result = [(0, 0, values)]

        return result

    teacher_ids = fields.Many2manyView(
        string='Teachers',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Teachers who teach this training session',
        comodel_name='academy.teacher',
        relation='academy_training_session_teacher_rel',
        column1='session_id',
        column2='teacher_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    teacher_count = fields.Integer(
        string='Teacher count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Total number of related teachers',
        compute='_compute_teacher_count'
    )

    @api.depends('teacher_assignment_ids')
    def _compute_teacher_count(self):
        for record in self:
            record.teacher_count = len(record.teacher_assignment_ids)

    primary_teacher_id = fields.Many2one(
        string='Primary instructor',
        required=False,
        readonly=True,
        index=True,
        help='Ultimately responsible for providing instruction',
        default=False,
        comodel_name='academy.teacher',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_primary_teacher_id',
        store=True,
        track_visibility='onchange'
    )

    @api.depends('teacher_assignment_ids')
    def _compute_primary_teacher_id(self):
        for record in self:
            assign_set = record.teacher_assignment_ids
            if not assign_set:
                record.primary_teacher_id = None
            else:
                sequence = min(assign_set.mapped('sequence'))
                assign = assign_set.filtered(lambda x: x.sequence == sequence)
                record.primary_teacher_id = assign[0].teacher_id

    reservation_ids = fields.One2many(
        string='Reservations',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Related facility reservations',
        comodel_name='facility.reservation',
        inverse_name='session_id',
        domain=[],
        context={'default_state': 'requested'},
        auto_join=False,
        limit=None,
        track_visibility='onchange',
        copy=False
    )

    primary_reservation_id = fields.Many2one(
        string='Primary reservation',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Primary facility reservation',
        comodel_name='facility.reservation',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_primary_reservation_id'
    )

    @api.depends('reservation_ids')
    def _compute_primary_reservation_id(self):
        for record in self:
            reservation_set = record.reservation_ids
            if not reservation_set:
                record.primary_reservation_id = None
            else:
                sequence = min(reservation_set.mapped('sequence'))
                reservation = reservation_set.filtered(
                    lambda x: x.sequence == sequence)
                record.primary_reservation_id = reservation[0]

    primary_facility_id = fields.Many2one(
        string='Primary facility',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Main facility where the training session will take place',
        comodel_name='facility.facility',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_primary_facility_id',
        store=True,
        track_visibility='onchange'
    )

    @api.depends('reservation_ids')
    def _compute_primary_facility_id(self):
        for record in self:
            reservation_set = record.reservation_ids
            if not reservation_set:
                record.primary_facility_id = None
            else:
                sequence = min(reservation_set.mapped('sequence'))
                reservation = reservation_set.filtered(
                    lambda x: x.sequence == sequence)
                record.primary_facility_id = reservation[0].facility_id

    primary_complex_id = fields.Many2one(
        string='Primary complex',
        related='primary_facility_id.complex_id',
        store=True
    )

    reservation_count = fields.Integer(
        string='Reservation count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Total number of facility reservations required for this session',
        compute='_compute_reservation_count',
        search='_search_reservation_count'
    )

    @api.depends('reservation_ids')
    def _compute_reservation_count(self):
        for record in self:
            record.reservation_count = len(record.reservation_ids)

    @api.model
    def _search_reservation_count(self, operator, value):
        raise UserError(_('No implemented yet'))
        return TRUE_DOMAIN

    invitation_ids = fields.One2many(
        string='Invitation',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='List of attendees for the session',
        comodel_name='academy.training.session.invitation',
        inverse_name='session_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        track_visibility='onchange',
        copy=False
    )

    invitation_count = fields.Integer(
        string='Invitation count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of students have been invited to the session',
        compute='_compute_invitation_count',
        search='_search_invitation_count',
        store=False
    )

    @api.depends('invitation_ids')
    def _compute_invitation_count(self):
        for record in self:
            record.invitation_count = len(record.invitation_ids)

    @api.model
    def _search_invitation_count(self, operator, value):
        return TRUE_DOMAIN

    date_start = fields.Datetime(
        string='Beginning',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.now_o_clock(round_up=True),
        help='Date/time of session start',
        track_visibility='onchange'
    )

    @api.onchange('date_start')
    def _onchange_beginning(self):
        self._compute_duration()

    date_stop = fields.Datetime(
        string='Ending',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.now_o_clock(offset_hours=1, round_up=True),
        help='Date/time of session end',
        track_visibility='onchange'
    )

    @api.onchange('date_stop')
    def _onchange_ending(self):
        self._compute_duration()

    @staticmethod
    def now_o_clock(offset_hours=0, round_up=False):
        present = fields.datetime.now()
        oclock = present.replace(minute=0, second=0, microsecond=0)

        if round_up and (oclock < present):  # almost always
            oclock += timedelta(hours=1)

        return oclock + timedelta(hours=offset_hours)

    date_delay = fields.Float(
        string='Duration',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Time length of the training session',
        store=True,
        compute='_compute_duration',
        group_operator='sum'
    )

    @api.onchange('date_delay')
    def _onchange_duration(self):
        for record in self:
            if record._origin.date_delay != record.date_delay:
                span = record.date_delay * 3600.0
                record.date_stop = record.date_start + timedelta(seconds=span)

    @api.depends('date_start', 'date_stop')
    def _compute_duration(self):
        for record in self:
            delay = record._time_interval(record.date_start, record.date_stop)
            record.date_delay = delay

    def date_delay_str(self, span=None):
        self.ensure_one()

        if span is None:
            span = (self.date_delay or 0)

        hours = int(span)
        pattern = '{h:02d} h'

        span = (span % 1)
        minutes = int(span * 60)
        if minutes:
            pattern += ' {m:02d}\''

        span = ((span * 60) % 1)
        seconds = int(span * 60)
        if seconds:
            pattern += ' {s:02d}\"'

        return pattern.format(h=hours, m=minutes, s=seconds)

    interval_str = fields.Char(
        string='Interval',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Display session time interval',
        size=24,
        translate=False,
        compute='_compute_interval_str'
    )

    @api.depends('date_start', 'date_stop')
    def _compute_interval_str(self):

        for record in self:
            second = record.date_start.second or record.date_stop.second
            tformat = '%H:%M:%S' if second else '%H:%M'

            left = record.date_start.strftime(tformat)
            right = record.date_stop.strftime(tformat)

            record.interval_str = '{} - {}'.format(left, right)

    validate = fields.Boolean(
        string='Validate',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='If checked, the event date range will be checked before saving'
    )

    exclusion_ids = fields.One2many(
        string='Exclusions',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='List with studentswho have not been invited',
        comodel_name='academy.training.session.affinity',
        inverse_name='session_id',
        domain=[("invited", "<>", True)],
        context={},
        auto_join=False,
        limit=None
    )

    exclusion_count = fields.Integer(
        string='Exclusion count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of students have not been invited to the session',
        compute='_compute_exclusion_count',
        search='_search_exclusion_count',
        store=False
    )

    @api.depends('exclusion_ids')
    def _compute_exclusion_count(self):
        for record in self:
            record.exclusion_count = len(record.exclusion_ids)

    @api.model
    def _search_exclusion_count(self, operator, value):
        sql = '''
            SELECT
                ats."id" AS session_id,
                SUM(
                    (tsa."id" IS NOT NULL AND tsa.invited IS NOT TRUE)::INTEGER
                )::INTEGER AS exclusion_count
            FROM
                academy_training_session AS ats
            LEFT JOIN academy_training_session_affinity AS tsa
                    ON tsa.session_id = ats."id"
            WHERE
                    ats.active AND ats.training_action_id IS NOT NULL
            GROUP BY ats."id"
            HAVING SUM(
                (tsa."id" IS NOT NULL AND tsa.invited IS NOT TRUE)::INTEGER
            )::INTEGER {operator} {value}
        '''

        domain = FALSE_DOMAIN

        if value is True:
            operator = '>' if operator == '=' else '='
            value = 0
        elif value is False:  # Field is mandatory
            operator = '=' if operator == '=' else '>'
            value = 0

        sql = sql.format(operator=operator, value=value)
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()

        if results:
            session_ids = [item['session_id'] for item in results]
            domain = [('id', 'in', session_ids)]

        return domain

    lang = fields.Char(
        string='Language',
        required=True,
        readonly=True,
        index=False,
        help=False,
        size=255,
        translate=False,
        compute='_compute_lang',
        store=False
    )

    @api.depends_context('uid')
    @api.depends('primary_teacher_id')
    def _compute_lang(self):
        """ Gets the language used by the current user and sets it as `lang`
            field value
        """

        user_id = self.env['res.users'].browse(self.env.uid)

        for record in self:
            record.lang = user_id.lang

    allow_overlap = fields.Boolean(
        string='Allow overlap',
        related='training_action_id.allow_overlap',
        store=True
    )

    _sql_constraints = [
        (
            'check_training_task',
            CHECK_TRAINING_TASK,
            _('Teaching sessions must be linked to a competency unit')
        ),
        (
            'check_non_training_task',
            CHECK_NON_TRAINING_TASK,
            _('Non-teaching sessions must be linked to a task')
        ),
        (
            'unique_training_action_id',
            '''EXCLUDE USING gist (
                training_action_id WITH =,
                tsrange ( date_start, date_stop ) WITH &&
            ) WHERE (validate AND allow_overlap IS NOT TRUE);
            -- Requires btree_gist''',
            _('This event overlaps with another of the same training action '
              'action')
        ),
        (
            'positive_interval',
            'CHECK(date_start < date_stop)',
            _('Session cannot end before starting')
        )
    ]

    def _track_subtype(self, init_values):
        self.ensure_one()

        fields = ['date_start', 'date_stop', 'active', 'state',
                  'training_action_id', 'task_id', 'competency_unit_id',
                  'primary_teacher_id', 'primary_facility_id',
                  'teacher_assignment_ids', 'reservation_ids']

        xid = 'academy_timesheets.{}'
        result = False

        if self.state != 'draft' and any(key in fields for key in init_values):
            xid = xid.format('academy_timesheets_training_session_changed')
            result = self.env.ref(xid)
        elif init_values.get('state', False) == 'ready':
            xid = xid.format('academy_timesheets_training_session_draft')
            result = self.env.ref(xid)
        else:
            _super = super(AcademyTrainingSession, self)
            result = _super._track_subtype(init_values)

        return result

    def get_tz(self):
        """Retrieve session timezone if available.

        The timezone can correspond, in order of priority, to:
        1) The complex pertaining to the main classroom.
        2) The company associated with the session.
        3) The administrator of the session.
        4) Default to Coordinated Universal Time (UTC).

        Returns:
            pytz.timezone: Timezone instance or UTC if not found.
        """

        self.ensure_one()

        tz = self.mapped('primary_facility_id.complex_id.partner_id.tz')
        if not tz:
            tz = self.mapped('company_id.partner_id.tz')
        if not tz:
            tz = self.mapped('manager_id.partner_id.tz')

        tz = tz and tz[0] or 'UTC'  # First value in list or 'UTC'

        return pytz.timezone(tz)

    def _get_session_timezone(self, message):
        """
        Retrieve session timezone if available. It will be used to communicate
        time changes to the teachers involved in the session. See: ``get_tz``

        Args:
            message (mail.message): The message object.

        Returns:
            pytz.timezone: Timezone instance or UTC if not found.
        """

        try:
            session = self.env[message.model].browse(message.res_id)
            return session.get_tz() if session else False

        except Exception:
            msg = _('Session with id #{} not found')
            _logger.error(msg.format(message.res_id))
            return None

    @staticmethod
    def localized_dt(value, tz, show_tz=False):
        """
        Converts and localizes a given datetime or date value to the specified
        timezone.

        This method will be used by ``_notify_prepare_template_context`` to
        adjust the display of dates and times in email notifications based on
        the session's timezone.

        Args:
            value (date | datetime): Date or datetime value to be localized.
            tz (str): Timezone identifier string, e.g., 'Europe/Madrid'.
            show_tz (bool, optional): If set to True, appends the timezone name
                                      to the resulting string representation.

        Returns:
            str: Localized string representation of the given date or datetime
                 value.
        """

        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, date):
            dt = datetime.combine(value, time.min)
        else:
            return value

        dt = pytz.utc.localize(dt)
        dt = dt.astimezone(tz)

        if isinstance(value, datetime):
            result = dt.strftime('%c')
        else:
            result = dt.date().strftime('%x')

        if show_tz:
            result = '{} ({})'.format(result, _(tz.zone))

        return result

    def _notify_get_reply_to(self, default=None, records=None, company=None,
                             doc_names=None):
        """
        Overwrite the reply-to address in email notifications.

        For each Academy Training Session record, the reply-to address is set
        to the email of the user responsible for the session (manager_id).

        Args:
            default (str, optional): Default reply-to address.
            records (recordset, optional): The set of records for which the
                                           reply-to address should be computed.
            company (res.company, optional): The company in context.
            doc_names (dict, optional): Dictionary with document names.

        Returns:
            dict: A mapping of record IDs to their reply-to addresses.
        """

        parent = super(AcademyTrainingSession, self)
        result = parent._notify_get_reply_to(
            default, records, company, doc_names)

        records = records or self
        if not result or not isinstance(result, dict) or not records:
            return result

        partner_path = 'manager_id.partner_id'
        for record in records:
            if record.id not in result:
                continue

            partner = record.mapped(partner_path)
            if not partner or not partner.email_normalized:
                continue

            email = partner.email_normalized
            if partner.name:
                email = '{} <{}>'.format(partner.name, email)

            result[record.id] = email

        return result

    @api.model
    def _notify_prepare_template_context(self, message, msg_vals,
                                         model_description=False,
                                         mail_auto_delete=True):
        """
        Adjust the date and time values in tracking values of notifications
        to reflect the timezone of the session where the event is taking place.

        This method customizes the context used for notification templates.
        When a tracked field of type 'date' or 'datetime' changes, it modifies
        the displayed value to show it in the session's timezone, ensuring
        that email recipients see the correct localized time of the session.

        Args:
            message (Model): Mail message record containing tracking values
            msg_vals (dict): Dictionary with the values for message creation
            model_description (str, optional): Optional model description for
                                               notifications
            mail_auto_delete (bool, optional): Flag indicating whether to
                                               auto-delete the mail

        Returns:
            dic: Updated template context with localized date and time values
        """

        parent = super(AcademyTrainingSession, self)
        result = parent._notify_prepare_template_context(
            message, msg_vals, model_description, mail_auto_delete)

        track_values = (result or {}).get('tracking_values', False)
        if not track_values:
            return result

        track_set = message.mapped('tracking_value_ids').filtered(
            lambda r: r.field_type in ('date', 'datetime'))
        if not track_set:
            return result

        session_tz = self._get_session_timezone(message)
        for idx, values in enumerate(track_values):
            caption = values[0]

            track = track_set.filtered(lambda r: r.field_desc == caption)
            if not track:
                continue

            track = track[0]
            old_value = self.localized_dt(
                track.old_value_datetime, session_tz)
            new_value = self.localized_dt(
                track.new_value_datetime, session_tz, show_tz=True)

            result['tracking_values'][idx] = (caption, old_value, new_value)

        return result

    def _notify_record_by_email(self, message, recipients_data, msg_vals=False,
                                model_description=False, mail_auto_delete=True,
                                check_existing=False, force_send=True,
                                send_after_commit=True, **kwargs):
        """
        Override to set a custom email layout for notifications.

        It also prevents emails from being sent notifying changes when there is
        no record of the values that have been altered.

        This method modifies the email layout for notifications related
        to Academy Training Sessions. It sets the layout to
        'academy_timesheets.academy_session_notification_email'.
        """

        # Allow to skipe email notifications using context
        if self.env.context.get('skip_email_notification', False):
            return True

        # Prevents empty notifations will be sent by email
        if not msg_vals or not message.tracking_value_ids:
            return True

        # Changes email template will be used send notifications
        msg_vals['email_layout_xmlid'] = \
            'academy_timesheets.academy_session_notification_email'

        parent = super(AcademyTrainingSession, self)
        return parent._notify_record_by_email(
            message, recipients_data, msg_vals, model_description,
            mail_auto_delete, check_existing, force_send, send_after_commit,
            **kwargs)

    def _notify_compute_recipients(self, message, msg_vals=None):
        """
        Override to include training session teachers as recipients.

        This method ensures that all teachers related to the
        Academy Training Session are included in the recipients list,
        without duplicating if they are already followers.

        Args:
            message (mail.message): The message being sent.
            msg_vals (dict, optional): Additional message values.

        Returns:
            dict: Computed recipient data with partners and channels.
        """

        parent = super(AcademyTrainingSession, self)
        result = parent._notify_compute_recipients(message, msg_vals)

        draft_subtype_id = ('academy_timesheets.'
                            'academy_timesheets_training_session_draft')
        changed_subtype_id = ('academy_timesheets.'
                              'academy_timesheets_training_session_changed')
        subtype_set = \
            self.env.ref(draft_subtype_id) + self.env.ref(changed_subtype_id)

        if message.subtype_id in subtype_set:

            if result and 'partners' in result:
                follower_partner_ids = \
                    [item['id'] for item in result['partners']]
            else:
                follower_partner_ids = []

            for record in self:
                teacher_users = record.mapped('teacher_ids.res_users_id')

                for user in teacher_users:
                    partner = user.partner_id

                    if partner.id in follower_partner_ids:
                        continue

                    result['partners'].append({
                        'id': partner.id,
                        'active': True,
                        'share': False,
                        'groups': user.groups_id.ids,
                        'notif': 'email',
                        'type': 'user'
                    })

        return result

    @staticmethod
    def _time_interval(start, stop):
        if start and stop:
            difference = (stop - start)
            value = max(difference.total_seconds(), 0)
        else:
            value = 0

        return value / 3600.0

    @api.model
    def _read_help_to_fill_configuration(self):
        config = self.env['ir.config_parameter'].sudo()
        help_to_fill = config.get_param(
            'academy_timesheets.help_to_fill', False)
        wait_to_fill = config.get_param(
            'academy_timesheets.wait_to_fill', '0.0')

        return help_to_fill, safe_eval(wait_to_fill)

    @api.model
    def _get_last_session(self, teacher_id, seconds):
        now = fields.Datetime.now() - timedelta(seconds=seconds)
        tformat = '%Y-%m-%d %H:%M:%S'

        domain = [
            '&',
            ('primary_teacher_id', '=', teacher_id),
            ('create_date', '>=', now.strftime(tformat))
        ]
        session_obj = self.env['academy.training.session']
        return session_obj.search(
            domain, order="create_date DESC", limit=1)

    @staticmethod
    def _serialize_session(session):
        tformat = '%Y-%m-%d %H:%M:%S'

        values = {
            'state': session.state,
            'task_name': session.task_name,
            'description': session.description,
            'kind': session.kind,
            'validate': session.validate,
            'task_id': session.task_id.id,
            'training_action_id': session.training_action_id.id,
            'competency_unit_id': session.competency_unit_id.id,
            'teacher_assignment_ids': [(5, 0, 0)],
            'reservation_ids': [(5, 0, 0)],
            'invitation_ids': [(5, 0, 0)]
        }

        for assign in session.teacher_assignment_ids:
            m2m_op = (0, 0, {
                'teacher_id': assign.teacher_id.id,
                'sequence': assign.sequence
            })
            values['teacher_assignment_ids'].append(m2m_op)

        for reservation in session.reservation_ids:
            m2m_op = (0, 0, {
                'date_start': reservation.date_start.strftime(tformat),
                'date_stop': reservation.date_stop.strftime(tformat),
                'sequence': reservation.sequence,
                'facility_id': reservation.facility_id.id,
                'owner_id': reservation.owner_id.id,
                'subrogate_id': reservation.subrogate_id.id,
                'state': reservation.state
            })
            values['reservation_ids'].append(m2m_op)

        for invitation in session.invitation_ids:
            m2m_op = (0, 0, {
                'session_id': invitation.session_id.id,
                'enrolment_id': invitation.enrolment_id.id,
                'active': invitation.active,
            })
            values['invitation_ids'].append(m2m_op)

        return values

    @api.model
    def default_get(self, field_list):
        parent = super(AcademyTrainingSession, self)
        values = parent. default_get(field_list)

        help_to_fill, wait_to_fill = self._read_help_to_fill_configuration()
        teacher_id = self.env.context.get('default_primary_teacher_id', False)

        if help_to_fill and wait_to_fill > 0 and teacher_id:
            session = self._get_last_session(teacher_id, wait_to_fill * 3600)
            if session and session.task_id:
                session_data = self._serialize_session(session)
                values.update(session_data)

        return values

    def name_get(self):
        result = []

        for record in self:
            if self.env.context.get('name_get_session_interval', False):
                date_base = record.date_start.strftime('%d-%m-%Y')
                time_start = record.date_start.strftime('%H:%M')
                time_stop = record.date_stop.strftime('%H:%M')

                name = '{} ({} - {})'.format(date_base, time_start, time_stop)

            elif self.env.context.get('default_training_action_id', False):
                if record.competency_unit_id:
                    name = record.competency_unit_id.competency_name
                else:
                    name = _('New session')
            else:
                if record.training_action_id:
                    name = record.training_action_id.action_name
                elif record.task_id:
                    name = record.task_id.name
                else:
                    name = _('New session')

            result.append((record.id, name))

        return result

    # @api.model
    # def _where_calc(self, domain, active_test=True):
    #     if not any(item[0] == 'state' for item in domain):
    #         domain = [('state', '=', 'ready')] + domain

    #     _super = super(AcademyTrainingSession, self)
    #     return _super._where_calc(domain, active_test)

    def view_timesheets(self):
        action_xid = ('academy_timesheets.'
                      'action_academy_training_session_timesheet_act_window')
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))

        if self:
            domain = [('training_session_id', 'in', self.mapped('id'))]
        else:
            domain = TRUE_DOMAIN

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': action.res_model,
            'target': action.target,
            'name': action.name,
            'view_mode': action.view_mode,
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    def view_invitation(self):
        self.ensure_one()

        action_xid = 'academy_timesheets.action_invitation_act_window'
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({'default_session_id': self.id})

        domain = [('session_id', '=', self.id)]

        view_modes = action.view_mode.split(',')
        view_modes = [mode for mode in view_modes if mode != 'tree']
        view_modes.insert(0, 'tree')

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.training.session.invitation',
            'target': 'current',
            'name': _('Invitations'),
            'view_mode': ','.join(view_modes),
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    def view_exclusion(self):
        self.ensure_one()

        action_xid = 'academy_timesheets.action_affinity_act_window'
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({'default_session_id': self.id})

        domain = [
            ('session_id', '=', self.id),
            ("invited", "<>", True)
        ]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.training.session.affinity',
            'target': 'current',
            'name': _('Exclusions'),
            'view_mode': action.view_mode,
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    def view_reservations(self):
        self.ensure_one()

        action_xid = 'facility_management.action_reservations_act_window'
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({
            'default_session_id': self.id,
            'default_date_start': self.date_start,
            'default_date_stop': self.date_stop,
        })

        domain = [
            ('session_id', '=', self.id)
        ]

        view_modes = action.view_mode.split(',')
        view_modes = [item for item in view_modes if item != 'calendar']

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': 'facility.reservation',
            'target': 'current',
            'name': _('Reservations'),
            'view_mode': ','.join(view_modes),
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    def view_teachers(self):
        self.ensure_one()

        action_xid = 'academy_base.action_teacher_act_window'
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({'default_session_id': self.id})
        ctx.update({'create': False, 'delete': False, 'edit': False})

        domain = [
            ('session_ids.id', '=', self.id)
        ]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': action.res_model,
            'target': 'current',
            'name': _('Teachers'),
            'view_mode': action.view_mode,
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    def invite_all(self):
        enrol_obj = self.env['academy.training.action.enrolment']
        invitation_obj = self.env['academy.training.session.invitation']

        for record in self:
            invitation_ops = []

            date_start = record.date_start.strftime(DATE_FORMAT)
            date_stop = record.date_stop.strftime(DATE_FORMAT)

            enrol_domain = [
                '&',
                '&',
                '&',
                ('training_action_id', '=', record.training_action_id.id),
                ('competency_unit_ids', '=', record.competency_unit_id.id),
                ('register', '<=', date_start),
                '|',
                ('deregister', '=', False),
                ('deregister', '>=', date_stop)
            ]

            enrol_set = enrol_obj.search(enrol_domain)

            for enrol in enrol_set:
                domain = [
                    ('session_id', '=', record.id,),
                    ('enrolment_id', '=', enrol.id)
                ]
                invitation = invitation_obj.search(domain, limit=1)

                if invitation:
                    o2m_op = (1, invitation.id, {'active': True})
                else:
                    o2m_op = (0, 0, {
                        'session_id': record.id,
                        'enrolment_id': enrol.id,
                        'active': True
                    })

                invitation_ops.append(o2m_op)

            record.write({'invitation_ids': invitation_ops})

    @api.model
    def create(self, values):
        tracking_disable_ctx = self.env.context.copy()
        tracking_disable_ctx.update({'tracking_disable': True})

        self._update_task_name(values)

        self_ctx = self.with_context(tracking_disable_ctx)
        with self.env.cr.savepoint():
            self_ctx._adjust_existing_facility_reservations(values)

        if 'kind' in values:
            if values.get('kind', None) == 'teach':
                values['task_id'] = None
            else:
                values['training_action_id'] = None
                values['competency_unit_id'] = None

        _super = super(AcademyTrainingSession, self)
        result = _super.create(values)

        if 'invitation_ids' not in values:
            result.invite_all()

        if 'reservation_ids' in values:
            reservation_values = {
                'date_start': result.date_start,
                'date_stop': result.date_stop,
                'name': result.training_action_id.action_name,
                'description': result.competency_unit_id.name
            }

            result_ctx = result.with_context(tracking_disable_ctx)
            result_ctx.reservation_ids.write(reservation_values)

        # result._update_session_followers()

        return result

    def write(self, values):
        tracking_disable_ctx = self.env.context.copy()
        tracking_disable_ctx.update({'tracking_disable': True})
        self_ctx = self.with_context(tracking_disable_ctx)

        self._update_task_name(values)
        self._adjust_existing_facility_reservations(values)

        if 'kind' in values:
            if values.get('kind', None) == 'teach':
                values['task_id'] = None
            else:
                values['training_action_id'] = None
                values['competency_unit_id'] = None

        if 'competency_unit_id' in values and 'invitation_ids' not in values:
            values['invitation_ids'] = None

        _super = super(AcademyTrainingSession, self)
        result = _super.write(values)

        if 'competency_unit_id' in values and 'invitation_ids' not in values:
            self.invite_all()

        if self.reservation_ids:
            reservation_values = {}

            if 'date_start' in values:
                reservation_values['date_start'] = values.get('date_start')
            if 'date_stop' in values:
                reservation_values['date_stop'] = values.get('date_stop')

            if reservation_values:
                ctx = self.env.context.copy()
                ctx.update({
                    'active_model': self._name,
                    'active_ids': self.mapped('id'),
                    'tracking_disable': True
                })
                self_ctx.reservation_ids.write(reservation_values)

        # self._update_session_followers()

        return result

    # def _update_session_followers(self):
    #     path = ('teacher_assignment_ids.teacher_id.res_users_id.'
    #             'partner_id.id')

    #     for record in self:
    #         partner_ids = record.mapped(path)
    #         if record.state == 'ready':
    #             record.message_subscribe(partner_ids=partner_ids)

    def toggle_followers(self):

        path = ('teacher_assignment_ids.teacher_id.res_users_id.'
                'partner_id')

        current_partner = self.env.user.partner_id

        for record in self:
            suscribe_set = record.mapped(path) + current_partner

            keep_set = suscribe_set + record.owner_id.partner_id + \
                record.subrogate_id.partner_id

            unsuscribe_set = self.message_partner_ids.filtered(
                lambda r: r not in keep_set)

            if suscribe_set:
                partner_ids = suscribe_set.mapped('id')
                record.message_subscribe(partner_ids=partner_ids)

            if unsuscribe_set:
                partner_ids = unsuscribe_set.mapped('id')
                self.message_unsubscribe(partner_ids=partner_ids)

    def send_by_mail(self):
        """
        """
        context = self.env.context.copy()
        context.update({'include_schedule_url': True})

        tpl_xid = 'academy_timesheets.mail_template_training_session_details'
        email_template = self.env.ref(tpl_xid).with_context(context)

        send_mail = email_template.send_mail

        for record in self:
            teacher_set = self.mapped('teacher_assignment_ids.teacher_id')
            for teacher in teacher_set:
                address = '{} <{}>'.format(teacher.name, teacher.email)
                evalues = {'email_to': address}
                send_mail(record.id, email_values=evalues, force_send=True)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()

        default = dict(default or {})

        ctx = dict(self.env.context, tracking_disable=True)
        parent = super(AcademyTrainingSession, self.with_context(ctx))

        if 'date_start' not in default:
            date_start = self.date_start + timedelta(days=7)
            default['date_start'] = date_start.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date_start = fields.Datetime.from_string(default['date_start'])

        if 'date_stop' not in default:
            date_stop = self.date_stop + timedelta(days=7)
            default['date_stop'] = date_stop.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date_stop = fields.Datetime.from_string(default['date_stop'])

        default['date_delay'] = self._time_interval(date_start, date_stop)

        if 'state' not in default:
            default['state'] = 'draft'

        if 'invitation_ids' not in default:
            default['invitation_ids'] = []
            for inv in self.invitation_ids:
                values = {
                    'enrolment_id': inv.enrolment_id.id,
                    'student_id': inv.student_id.id,
                    'present': False
                }
                m2m_op = (0, 0, values)
                default['invitation_ids'].append(m2m_op)

        if 'teacher_assignment_ids' not in default:
            default['teacher_assignment_ids'] = []
            for ta in self.teacher_assignment_ids:
                values = {
                    'teacher_id': ta.teacher_id.id,
                    'sequence': ta.sequence
                }
                m2m_op = (0, 0, values)
                default['teacher_assignment_ids'].append(m2m_op)

        if 'reservation_ids' not in default:
            default['reservation_ids'] = []
            for rv in self.reservation_ids:
                facility = rv.facility_id
                values = {
                    'facility_id': facility.id,
                    'sequence': rv.sequence,
                    'date_start': default['date_start'],
                    'date_stop': default['date_stop'],
                    'state': rv.state
                }
                m2m_op = (0, 0, values)
                default['reservation_ids'].append(m2m_op)

        return parent.copy(default=default)

    def _update_task_name(self, values):
        action_id = self.env.context.get('default_training_action_id', False)
        action_id = values.get('training_action_id', action_id)
        if action_id:
            action_obj = self.env['academy.training.action']
            action_set = action_obj.browse(action_id)
            values['task_name'] = action_set.action_name

        task_id = self.env.context.get('default_task_id', False)
        task_id = values.get('task_id', task_id)
        if task_id:
            task_obj = self.env['academy.non.teaching.task']
            task_set = task_obj.browse(task_id)
            values['task_name'] = task_set.name

    def copy_all(self, default=None):
        target_set = self.env['academy.training.session']
        for record in self:
            target_set += record.copy(default)

        return target_set

    @staticmethod
    def _real_id(record_set, single=False):
        """ Return a list with no NewId's of a single no NewId
        """

        result = []

        if record_set and single:
            record_set.ensure_one()

        for record in record_set:
            if isinstance(record.id, models.NewId):
                result.append(record._origin.id)
            else:
                result.append(record.id)

        if single:
            result = result[0] if len(result) == 1 else None

        return result

    def toogle_state(self, force_to=None):
        for record in self:
            if force_to in ('draft', 'ready'):
                record.state = force_to
            elif record.state == 'draft':
                record.state = 'ready'
            else:  # Current state is ready
                record.state = 'draft'

    def _compute_view_mapping(self):
        view_names = [
            'view_academy_training_session_calendar_teacher_readonly',
            'view_academy_training_session_kanban_teacher_readonly',
            'view_academy_training_session_tree_teacher_readonly',
            'view_academy_training_session_form_teacher_readonly'
        ]

        view_mapping = []
        for view_name in view_names:
            xid = 'academy_timesheets.{}'.format(view_name)
            view = self.env.ref(xid)
            pair = (view.id, view.type)
            view_mapping.append(pair)

        return view_mapping

    @api.model
    def view_my_schedule(self):
        user_id = self.env.context.get('uid', False)

        domain = [('res_users_id', '=', user_id)]
        teacher_obj = self.env['academy.teacher']
        teacher = teacher_obj.search(domain, limit=1)

        if not teacher:
            msg = _('You currently do not have teaching activity.')
            raise UserError(msg)

        act_window = teacher.view_sessions(definitive=False)
        act_window.update(views=self._compute_view_mapping())

        return act_window

    def download_my_schedule(self):
        user_id = self.env.context.get('uid', False)

        domain = [('res_users_id', '=', user_id)]
        teacher_obj = self.env['academy.teacher']
        teacher = teacher_obj.search(domain, limit=1)

        if not teacher:
            msg = _('You currently do not have teaching activity.')
            raise UserError(msg)

        return {
            'name': _('My schedule'),
            'type': 'ir.actions.act_url',
            'url': '/academy-timesheets/teacher/schedule',
            'target': 'blank',
        }

    @api.model
    def wizard_search_for_available_facilities(self):
        return {
            'name': 'Search for available facilities ',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'wizard_facilities',
            'url': '/academy_timesheets/redirect/facilities'
        }

    @api.model
    def wizard_search_for_available_teachers(self):
        return {
            'name': 'Search for available facilities ',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'wizard_teachers',
            'url': '/academy_timesheets/redirect/teachers'
        }

    # -------------------------------------------------------------------------
    # Method: _adjust_existing_facility_reservations
    # -------------------------------------------------------------------------

    def _adjust_existing_facility_reservations(self, values):
        reservation_set = self.env['facility.reservation']

        for record in self:

            record_reservation_set = \
                record._search_for_overlapping_reservations(values)

            date_start, date_stop = record._compute_new_datetimes(values)

            for reservation in record_reservation_set:

                if record._is_entirely_encompasses(
                        reservation, date_start, date_stop):
                    record._entirely_encompasses(reservation)

                elif record._is_starts_before(
                        reservation, date_start, date_stop):
                    record._starts_before(reservation, date_stop)
                    reservation_set |= reservation

                elif record._is_ends_after(
                        reservation, date_start, date_stop):
                    record._ends_after(reservation, date_start)
                    reservation_set |= reservation

                elif record._is_partially_encompasses(
                        reservation, date_start, date_stop):
                    record._partially_encompasses(
                        reservation, date_start, date_stop)
                    reservation_set |= reservation

        return reservation_set

    @staticmethod
    def _is_entirely_encompasses(reservation, date_start, date_stop):
        return date_start <= reservation.date_start and \
            date_stop >= reservation.date_stop

    @staticmethod
    def _is_starts_before(reservation, date_start, date_stop):
        return date_start <= reservation.date_start and \
            date_stop < reservation.date_stop

    @staticmethod
    def _is_ends_after(reservation, date_start, date_stop):
        return date_start > reservation.date_start and \
            date_stop >= reservation.date_stop

    @staticmethod
    def _is_partially_encompasses(reservation, date_start, date_stop):
        return date_start > reservation.date_start and \
            date_stop < reservation.date_stop

    @staticmethod
    def _entirely_encompasses(reservation):
        """ ╔═══╗→
            ║   ║───┐
            ║ S ║ R │x  Reservation will be removed
            ╚═══╝───┘
        """
        reservation.unlink()

    @staticmethod
    def _starts_before(reservation, date_stop):
        """ ╔═══╗
            ║ S ║───┐↓  Reservation will be reduced towards the end date
            ╚═══╝ R │
             →  └───┘
        """
        if reservation.date_stop > date_stop:
            date_start = fields.Datetime.to_string(date_stop)
            reservation.write({'date_start': date_start, 'scheduler_id': None})
        else:
            reservation.unlink()

    @staticmethod
    def _ends_after(reservation, date_start):
        """  →  ┌───┐
            ╔═══╗ R │
            ║ S ║───┘↑  Reservation will be reduced towards the start date
            ╚═══╝
        """
        if reservation.date_start < date_start:
            date_stop = fields.Datetime.to_string(date_start)
            reservation.write({'date_stop': date_stop, 'scheduler_id': None})
        else:
            reservation.unlink()

    def _partially_encompasses(self, reservation, date_start, date_stop):
        """     ┌───┐   ┌─¹─┐
            ╔═══╗   │↑  └───┘ Old reservation
            ║ S ║ R │
            ╚═══╝   │   ┌───┐
            →   └───┘   └─²─┘ New empty reservation
        """
        top_date_stop = fields.Datetime.to_string(reservation.date_stop)

        reservation.write({
            'date_stop': fields.Datetime.to_string(date_start),
            'scheduler_id': None
        })

        reservation_obj = self.env['facility.reservation']
        values = {
            'date_start': fields.Datetime.to_string(date_stop),
            'date_stop': top_date_stop,
            'training_action_id': self.training_action_id.id,
            'facility_id': reservation.facility_id.id,
            'scheduler_id': None
        }
        reservation_obj.create(values)

    # -------------------------------------------------------------------------
    # Method: _search_for_overlapping_reservations
    # -------------------------------------------------------------------------

    def _append_facility_domain(self, domains, values):
        facility_ids = self._catch_all_facilities(values)

        if facility_ids:
            same_facility_domain = [('facility_id', 'in', facility_ids)]
            domains.append(same_facility_domain)

    @staticmethod
    def _append_without_session_domain(domains):
        without_session_domain = [('session_id', '=', False)]
        domains.append(without_session_domain)

    def _append_training_action_domain(self, domains, values):
        training_action_id = values.get('training_action_id', False)
        if not training_action_id:
            training_action_id = self.training_action_id.id

        if training_action_id:
            same_training_action_domain = \
                [('training_action_id', '=', training_action_id)]
            domains.append(same_training_action_domain)
        else:
            message = 'A training action has not been found as expected'
            raise MissingError(message)

    def _append_overlapping_domain(self, domains, values):

        date_start, date_stop = \
            self._compute_new_datetimes(values, as_str=True)

        if date_start and date_stop:
            overlapped_domain = [
                '&',
                ('date_start', '<', date_stop),
                ('date_stop', '>', date_start)
            ]
            domains.append(overlapped_domain)
        else:
            message = ('The date range for the training session could not be '
                       'determined')
            raise MissingError(message)

    @staticmethod
    def _append_confirmed_domain(domains):
        state_confirmed_domain = [('state', '=', 'confirmed')]
        domains.append(state_confirmed_domain)

    def _search_for_overlapping_reservations(self, values):
        reservation_obj = self.env['facility.reservation']
        domains = []

        self._append_facility_domain(domains, values)
        if not domains:
            return reservation_obj

        self._append_without_session_domain(domains)
        self._append_training_action_domain(domains, values)
        self._append_overlapping_domain(domains, values)
        self._append_confirmed_domain(domains)

        domain = AND(domains)
        reservation_set = reservation_obj.search(domain)

        return reservation_set

    def _compute_new_datetimes(self, values, as_str=False):
        date_start = values.get('date_start', False) or self.date_start
        date_stop = values.get('date_stop', False) or self.date_stop

        if as_str:
            if isinstance(date_start, datetime):
                date_start = fields.Datetime.to_string(date_start)

            if isinstance(date_stop, datetime):
                date_stop = fields.Datetime.to_string(date_stop)
        else:
            if isinstance(date_start, str):
                date_start = fields.Datetime.from_string(date_start)

            if isinstance(date_stop, str):
                date_stop = fields.Datetime.from_string(date_stop)

        return date_start, date_stop

    # -------------------------------------------------------------------------
    # Method: _catch_all_facilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _catch_stock_method(stock, perform):
        if perform == 'add':
            return getattr(stock, 'update')
        elif perform == 'remove':
            return getattr(stock, 'difference_update')
        else:
            return None

    @staticmethod
    def _catch_from_values(stock, values):
        if values and isinstance(values, dict) and 'facility_id' in values:
            facility_id = values.get('facility_id', False)
            if facility_id:
                stock.add(facility_id)
                return [facility_id]

        return []

    @api.model
    def _catch_from_ids(self, stock, ids=None, perform='add', clear=False):

        if clear:
            stock.clear()

        if ids and isinstance(ids, (tuple, list, int)):
            reservation_obj = self.env['facility.reservation']
            reservation_set = reservation_obj.browse(ids)

            facility_ids = reservation_set.facility_id.ids
            if facility_ids:
                method = self._catch_stock_method(stock, perform)
                if method:
                    method(facility_ids)

                return facility_ids

        return []

    def _catch_all_facilities(self, values):
        """
            (0, 0,  { values }) link to a new record
            (1, ID, { values }) update the linked record with id = ID
            (2, ID)             remove and delete the linked record
            (3, ID)             cut the link to the linked record with id = ID
            (4, ID)             link to existing record with id = ID
            (5)                 unlink all (like using (3,ID)
            (6, 0, [IDs])       replace the list of linked IDs
        """

        facility_stock = set(self.mapped('reservation_ids.facility_id.id'))

        if values and 'reservation_ids' in values:
            m2m_ops = values.get('reservation_ids')

            for m2m_op in m2m_ops:
                if not (isinstance(m2m_op, (tuple, list)) and len(m2m_op) > 1):
                    continue

                if m2m_op[0] == 0 and len(m2m_op) > 2:
                    self._catch_from_values(facility_stock, m2m_op[2])

                elif m2m_op[0] == 1:
                    new_facility_ids = \
                        self._catch_from_values(facility_stock, m2m_op[2])
                    old_facility_ids = \
                        self._catch_from_ids(facility_stock, m2m_op[1])

                    if old_facility_ids and new_facility_ids and \
                       old_facility_ids[0] != new_facility_ids[0]:
                        facility_stock.difference_update(old_facility_ids)
                        facility_stock.update(new_facility_ids)

                elif m2m_op[0] in (2, 3):
                    self._catch_from_ids(
                        facility_stock, m2m_op[1], perform='remove')

                elif m2m_op[0] == 4:
                    self._catch_from_ids(facility_stock, m2m_op[1])

                elif m2m_op[0] == 5:
                    self._catch_from_ids(facility_stock, clear=True)

                elif m2m_op[0] == 6:
                    self._catch_from_ids(
                        facility_stock, m2m_op[2], clear=True)

        return list(facility_stock)
