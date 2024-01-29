# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, api
from odoo.tools.translate import _
from odoo.osv.expression import AND
from odoo.exceptions import UserError

from logging import getLogger
from datetime import datetime, timedelta, date

_logger = getLogger(__name__)


class AcademyTrainingSession(models.Model):
    """ Extends academy_timesheets.model_academy_training_session
    """

    _name = 'academy.training.session'
    _inherit = ['academy.training.session']

    @staticmethod
    def _midnight(dt):
        date_part = dt.date()
        time_part = datetime.min

        return datetime.combine(date_part, time_part)

    def _get_calendar_event_type(self):
        self.ensure_one()

        result = [(5, 0, 0)]
        xid = 'calendar_event_type_academy_timesheet'
        xid = 'academy_timesheets_to_calendar.{}'.format(xid)
        category = self.env.ref(xid)
        result.append((4, category.id, 0))

        if self.kind == 'teach':
            xid = 'calendar_event_type_academy_timesheet_teaching_task'
            xid = 'academy_timesheets_to_calendar.{}'.format(xid)
            category = self.env.ref(xid)
        else:
            xid = 'calendar_event_type_academy_timesheet_non_teaching'
            xid = 'academy_timesheets_to_calendar.{}'.format(xid)
            category = self.env.ref(xid)

        result.append((4, category.id, 0))

        return result

    def _get_primary_address(self):
        self.ensure_one()

        address = None
        if self.primary_facility_id:
            complex_id = self.primary_facility_id.complex_id
            partner = complex_id.partner_id

            parts = []

            if partner.street:
                parts.append(partner.street)
            if partner.street2:
                parts.append(partner.street2)
            if partner.zip:
                parts.append(partner.zip)
            if partner.city:
                parts.append(partner.city)
            if partner.state_id:
                parts.append(partner.state_id.name)
            if partner.country_id:
                parts.append(partner.country_id.name)

            if parts:
                address = ', '.join(parts)

        return address

    @staticmethod
    def midnight(dt):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def _build_event_values(self):
        self.ensure_one()

        result = {
            'name': self.display_name,
            'state': 'draft' if self.state == 'draft' else 'open',
            'start': self.midnight(self.date_start),
            'stop': self.midnight(self.date_stop),
            'allday': False,
            'start_datetime': self.date_start,
            'stop_datetime': self.date_stop,
            'duration': self.date_delay,
            'description': self.description,
            'location': self._get_primary_address(),
            'show_as': 'busy' if self.kind == 'teach' else 'free',
            'active': self.active,
            'categ_ids': self._get_calendar_event_type(),
        }

        return result

    def _update_event_create_values(self, values, user=None):
        alarm = self.env.ref('calendar.alarm_notif_1')
        user = user or self.env.user

        attendee_values = {
            'state': 'accepted',
            'partner_id': user.partner_id.id,
            'email': user.partner_id.email,
            'availability': 'busy' if self.kind == 'teach' else 'free'
        }

        values.update({
            'user_id': user.id,
            'session_id': self.id,
            'privacy': 'confidential',
            'recurrency': False,
            'partner_ids': [(5, 0, 0), (4, user.partner_id.id, 0)],
            'attendee_ids': [(5, 0, 0), (0, 0, attendee_values)],
            'alarm_ids': [(5, 0, 0), (4, alarm.id, 0)],
        })

    @api.model
    def _search_for_related_events(self, session_set, user=None):
        session_ids = session_set.mapped('id')

        ignore_active = ['|', ('active', '=', True), ('active', '!=', True)]
        in_session_set = [('session_id', 'in', session_ids)]

        domains = [ignore_active, in_session_set]

        if user:
            user_domain = [('user_id', '=', user.id)]
            domains.append(user_domain)

        event_domain = AND(domains)
        event_obj = self.env['calendar.event']
        event_set = event_obj.search(event_domain)

        return event_set

    @staticmethod
    def _session_has_user(session, user):
        path = 'teacher_assignment_ids.teacher_id.res_users_id.id'

        if session.teacher_assignment_ids:
            return user.id in session.mapped(path)

        return False

    def _save_event(self, event, user=False):
        self.ensure_one()

        values = self._build_event_values()

        if event:
            event.ensure_one()
            event.write(values)
        else:
            self._update_event_create_values(values, user)
            event.create(values)

        return event

    # def sync_interval_with_calendar(self, interval_type, user=None):
    #     today = date.today()

    #     if interval_type == 'day':
    #         date_start, date_stop = today, today

    #     elif interval_type == 'week':
    #         weekday = today.weekday()
    #         date_start = today - timedelta(days=weekday)
    #         date_stop = date_start + timedelta(days=6)

    #     elif interval_type == 'month':
    #         date_start = date(today.year, today.month, 1)

    #         next_month = date_start.replace(day=28) + timedelta(days=4)
    #         date_stop = next_month - timedelta(days=next_month.day)

    #     elif interval_type == 'year':
    #         date_start = date(today.year, today.month, 1)

    #         next_month = date_start.replace(day=28) + timedelta(days=4)
    #         date_stop = next_month - timedelta(days=next_month.day)

    #     else:
    #         msg = _('Unknown time iterval. Use: day, week, moth or year')
    #         raise UserError(msg)

    #     return self.sync_with_calendar(date_start, date_stop, user)

    @api.model
    def btn_syncronize(self, scale, date_start, date_stop, res_model, res_id):

        print(date_start, date_stop)
        date_start = datetime.strptime(date_start, "%Y-%m-%dT%H:%M:%SZ")
        date_stop = datetime.strptime(date_stop, "%Y-%m-%dT%H:%M:%SZ")

        assert date_start < date_stop, \
            _('The start date must be earlier than the end date')

        domain = [
            ('date_start', '>=', date_start),
            ('date_stop', '<=', date_stop)
        ]

        user = None
        if res_model == 'academy.teacher':
            field = 'teacher_assignment_ids.teacher_id'
            domain.append((field, '=', res_id))
            teacher_obj = self.env['academy.teacher']
            teacher = teacher_obj.browse(res_id)
            user = teacher.res_users_id if teacher else None

        elif res_model == 'academy.training.action':
            domain.append(('training_action_id', '=', res_id))

        print(res_model)

        session_obj = self.env['academy.training.session']
        session_set = session_obj.search(domain)

        return self.dump_to_calendar(session_set, user)

    @api.model
    def sync_with_calendar(self, date_start, date_stop, user=None):
        assert date_start < date_stop, \
            _('The start date must be earlier than the end date')

        domain = [
            ('date_start', '>=', date_start),
            ('date_stop', '<=', date_stop)
        ]

        if user:
            field = 'teacher_assignment_ids.teacher_id.res_users_id'
            domain.append((field, '=', user.id))

        session_obj = self.env['academy.training.sessions']
        session_set = session_obj.search(domain)

        return self.dump_to_calendar(session_set, user)

    @api.model
    def dump_to_calendar(self, session_set, user=None):
        """ Create calendar events related to the given training sessions.

        If an existing related calendar event already exists, this will be
        updated; otherwise, a new record will be created instead.

        The ``unique_session_by_user`` SQL constraint in the ``calendar.event``
        table prevents more than one event from being created for the same
        session. SO THERE IS NO NEED TO WORRY ABOUT EXISTING DUPLICATES.

        If an existing session is deleted, the ``ondelete='cascade'`` attribute
        in the "session_id" field of the ``calendar.event`` model would cause
        the related events to be removed. SO THERE IS NO NEED TO WORRY ABOUT
        DELETION.

        Args:
            session_set (Model): academy.training.session recordset
            user (Model, optional): single res.users record
        """

        event_set = self.env['calendar.event']

        if user and session_set:
            has_user = self._session_has_user
            session_set = session_set.filtered(lambda s: has_user(s, user))

        if session_set:

            event_set = self._search_for_related_events(session_set, user)

            for session in session_set:
                updatable_event_set = event_set.filtered(
                    lambda s: s.session_id.id == session.id)

                if user:
                    event_set += session._save_event(updatable_event_set)

                else:
                    for assign in session.teacher_assignment_ids:
                        user = assign.teacher_id.res_users_id

                        user_event = updatable_event_set.filtered(
                            lambda e: e.user_id == user.id)

                        event_set += session._save_event(user_event, user)

        return event_set
