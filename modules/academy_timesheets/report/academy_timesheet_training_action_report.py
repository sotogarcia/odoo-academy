# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models
from odoo.addons.academy_timesheets.lib.tools import truncate_name
from odoo.addons.academy_timesheets.lib.tools import truncate_to_space

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTimesheetTrainingActionReport(models.AbstractModel):
    """Custom report behavior"""

    _name = (
        "report.academy_timesheets."
        "view_academy_timesheet_training_action_qweb"
    )

    _inherit = ["time.span.report.mixin"]

    _table = "report_academy_timesheet_training_action"
    _description = "Academy timesheet training action report"

    def _read_record_values(self, session):
        action_line_id = session.action_line_id.name
        action_line_id = truncate_name(action_line_id, 64, 160)

        facility = session.primary_facility_id.name
        teacher = session.primary_teacher_id.name
        teacher = truncate_to_space(teacher, 5, 15, ellipsis=False)

        return {
            "id": session.id,
            "date": self.date_str(session.date_start),
            "interval": self.time_str(session),
            "action_line_id": action_line_id,
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

        action_obj = self.env["academy.training.action"]

        domain = [("id", "in", docids)]
        action_set = action_obj.search(domain)

        in_date = self._in
        values = {}

        for action in action_set:
            sessions = action.session_ids

            values[action.id] = {
                "id": action.id,
                "name": action.name,
                "weeks": {},
            }

            for current in self._date_range(date_start, date_stop, full_weeks):
                week = self._week_str(current)
                sessions = action.session_ids.filtered(
                    lambda s: in_date(s, current) and s.state == "ready"
                )

                if week not in values[action.id]["weeks"]:
                    values[action.id]["weeks"].update({week: {}})

                date_str = self.date_str(current)
                if date_str not in values[action.id]["weeks"][week]:
                    values[action.id]["weeks"][week].update({date_str: {}})

                for session in sessions:
                    values[action.id]["weeks"][week][date_str][
                        session.id
                    ] = self._read_record_values(session)

        docargs = {
            "doc_ids": docids,
            "doc_model": action_obj,
            "data": data,
            "docs": action_set,
            "report": self,
            "values": values,
            "lang": lang,
        }

        return docargs
