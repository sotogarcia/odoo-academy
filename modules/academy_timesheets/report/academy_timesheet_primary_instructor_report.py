# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models
from odoo.addons.academy_timesheets.lib.tools import truncate_name

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTimesheetPrimrayInstructorReport(models.AbstractModel):
    """ Custom report behavior
    """

    _name = ('report.academy_timesheets.'
             'view_academy_timesheet_primary_instructor_qweb')

    _inherit = ['time.span.report.mixin']

    _table = 'report_academy_timesheet_primary_instructor'
    _description = u'Academy timesheet teacher report'

    def _read_record_values(self, session):
        competency_unit = session.competency_unit_id.competency_name
        competency_unit = truncate_name(competency_unit, 64, 75)

        training_action = session.training_action_id.action_name
        facility = session.primary_facility_id.name

        return {
            'id': session.id,
            'date': self.date_str(session.date_start),
            'interval': self.time_str(session),
            'training_action': training_action,
            'task_name': session.task_name,
            'competency_unit': competency_unit,
            'facility': facility
        }

    def _get_report_values(self, docids, data=None):
        data = data or {}
        docids = docids or data.get('doc_ids', [])

        date_start, date_stop = self._get_interval(data)

        # full_weeks from ``data`` or from context
        full_weeks = self.env.context.get('full_weeks', True)
        full_weeks = data.get('full_weeks', full_weeks)

        lang = self._get_lang()

        teacher_obj = self.env['academy.teacher']

        domain = [('id', 'in', docids)]
        teacher_set = teacher_obj.search(domain)

        in_date = self._in
        values = {}

        for teacher in teacher_set:
            sessions = teacher.session_ids

            values[teacher.id] = {
                'id': teacher.id,
                'name': teacher.name,
                'weeks': {}
            }

            for current in self._date_range(date_start, date_stop, full_weeks):

                week = self._week_str(current)
                sessions = teacher.session_ids.filtered(
                    lambda s: in_date(s, current) and s.state == 'ready')

                if week not in values[teacher.id]['weeks']:
                    values[teacher.id]['weeks'].update({week: {}})

                date_str = self.date_str(current)
                if date_str not in values[teacher.id]['weeks'][week]:
                    values[teacher.id]['weeks'][week].update({date_str: {}})

                for session in sessions:
                    values[teacher.id]['weeks'][week][date_str][session.id] = \
                        self._read_record_values(session)

        docargs = {
            'doc_ids': docids,
            'doc_model': teacher_obj,
            'data': data,
            'docs': teacher_set,
            'report': self,
            'values': values,
            'lang': lang
        }

        return docargs
