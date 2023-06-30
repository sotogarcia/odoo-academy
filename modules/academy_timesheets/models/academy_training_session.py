# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools import safe_eval
from odoo.tools.translate import _
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import UserError

from datetime import timedelta

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
        related='training_action_id.company_id',
        store=True
    )

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
        auto_join=False
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
        store=True
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
        context={},
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
        store=True
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

            enrol_domain = [
                ('training_action_id', '=', record.training_action_id.id),
                ('competency_unit_ids', '=', record.competency_unit_id.id)
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

        self._update_task_name(values)

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
            result.reservation_ids.write(reservation_values)

        return result

    def write(self, values):

        self._update_task_name(values)

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
                    'active_ids': self.mapped('id')
                })
                self_ctx = self.with_context(ctx)
                self_ctx.reservation_ids.write(reservation_values)

        return result

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})

        if 'date_start' not in default:
            date_start = self.date_start + timedelta(days=7)
            default['date_start'] = date_start.strftime('%Y-%m-%d %H:%M:%S')
        if 'date_stop' not in default:
            date_stop = self.date_stop + timedelta(days=7)
            default['date_stop'] = date_stop.strftime('%Y-%m-%d %H:%M:%S')

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
                    'date_stop': default['date_stop']
                }
                m2m_op = (0, 0, values)
                default['reservation_ids'].append(m2m_op)

        return super(AcademyTrainingSession, self).copy(default=default)

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

        act_window = teacher.view_sessions()
        act_window.update(views=self._compute_view_mapping())

        print(act_window)

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
