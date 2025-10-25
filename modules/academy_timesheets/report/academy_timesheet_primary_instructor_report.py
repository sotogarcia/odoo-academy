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
    """Custom report behavior"""

    _name = (
        "report.academy_timesheets."
        "view_academy_timesheet_primary_instructor_qweb"
    )

    _inherit = ["time.span.report.mixin"]

    _table = "report_academy_timesheet_primary_instructor"
    _description = "Academy timesheet teacher report"

    def _read_record_values(self, session):
        action_line_id = session.action_line_id.name
        action_line_id = truncate_name(action_line_id, 64, 75)

        training_action = session.training_action_id.name
        facility = session.primary_facility_id.name

        return {
            "id": session.id,
            "date": self.date_str(session.date_start),
            "interval": self.time_str(session),
            "training_action": training_action,
            "display_name": session.display_name,
            "action_line_id": action_line_id,
            "facility": facility,
        }

    def _get_report_values(self, docids, data=None):
        data = data or {}
        docids = docids or data.get("doc_ids", [])

        date_start, date_stop = self._get_interval(data)

        # full_weeks from ``data`` or from context
        full_weeks = self.env.context.get("full_weeks", True)
        full_weeks = data.get("full_weeks", full_weeks)

        lang = self.get_lang()

        teacher_obj = self.env["academy.teacher"]

        domain = [("id", "in", docids)]
        teacher_set = teacher_obj.search(domain)

        in_date = self.date_in
        values = {}

        for teacher in teacher_set:
            sessions = teacher.session_ids

            values[teacher.id] = {
                "id": teacher.id,
                "name": teacher.name,
                "weeks": {},
            }

            for current in self.date_range(date_start, date_stop, full_weeks):
                week = self.week_str(current)
                sessions = teacher.session_ids.filtered(
                    lambda s: in_date(s, current) and s.state == "ready"
                )

                if week not in values[teacher.id]["weeks"]:
                    values[teacher.id]["weeks"].update({week: {}})

                date_str = self.date_str(current)
                if date_str not in values[teacher.id]["weeks"][week]:
                    values[teacher.id]["weeks"][week].update({date_str: {}})

                for session in sessions:
                    values[teacher.id]["weeks"][week][date_str][
                        session.id
                    ] = self._read_record_values(session)

        docargs = {
            "doc_ids": docids,
            "doc_model": teacher_obj,
            "data": data,
            "docs": teacher_set,
            "report": self,
            "values": values,
            "lang": lang,
        }

        return docargs
