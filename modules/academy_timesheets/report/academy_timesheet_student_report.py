# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models
from logging import getLogger
from odoo.addons.academy_timesheets.lib.tools import truncate_name
from odoo.addons.academy_timesheets.lib.tools import truncate_to_space

_logger = getLogger(__name__)


class AcademyTimesheetStudentReport(models.AbstractModel):
    """Custom report behavior"""

    _name = "report.academy_timesheets." "view_academy_timesheet_student_qweb"

    _inherit = ["time.span.report.mixin"]

    _table = "report_academy_timesheet_student"
    _description = "Academy timesheet student report"

    def _read_record_values(self, session):
        training_action = session.training_action_id.name

        competency_unit = session.action_line_id.competency_name
        competency_unit = truncate_name(competency_unit, 64, 160)

        facility = session.primary_facility_id.name

        teacher = session.primary_teacher_id.name
        teacher = truncate_to_space(teacher, 5, 15, ellipsis=False)

        return {
            "id": session.id,
            "date": self.date_str(session.date_start),
            "interval": self.time_str(session),
            "training_action": training_action,
            "competency_unit": competency_unit,
            "facility": facility,
            "teacher": teacher,
        }

    def _get_report_values(self, docids, data=None):
        data = data or {}
        docids = docids or data.get("doc_ids", [])

        date_start, date_stop = self._get_interval(data)

        # full_weeks from ``data`` or from context
        full_weeks = self.env.context.get("full_weeks", True)
        full_weeks = data.get("full_weeks", full_weeks)

        lang = self._get_lang()

        student_obj = self.env["academy.student"]

        domain = [("id", "in", docids)]
        student_set = student_obj.search(domain)

        in_date = self._in
        values = {}

        for student in student_set:
            sessions = student.session_ids

            values[student.id] = {
                "id": student.id,
                "name": student.name,
                "weeks": {},
            }

            for current in self._date_range(date_start, date_stop, full_weeks):
                week = self._week_str(current)
                sessions = student.session_ids.filtered(
                    lambda s: in_date(s, current) and s.state == "ready"
                )

                if week not in values[student.id]["weeks"]:
                    values[student.id]["weeks"].update({week: {}})

                date_str = self.date_str(current)
                if date_str not in values[student.id]["weeks"][week]:
                    values[student.id]["weeks"][week].update({date_str: {}})

                for session in sessions:
                    values[student.id]["weeks"][week][date_str][
                        session.id
                    ] = self._read_record_values(session)

        docargs = {
            "doc_ids": docids,
            "doc_model": student_obj,
            "data": data,
            "docs": student_set,
            "report": self,
            "values": values,
            "lang": lang,
        }

        return docargs
