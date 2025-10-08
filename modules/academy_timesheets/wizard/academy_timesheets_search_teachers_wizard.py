# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models
from odoo.tools.translate import _
from logging import getLogger
from odoo.osv.expression import AND
from odoo.tools.safe_eval import safe_eval

_logger = getLogger(__name__)


class AcademyTimesheetsSearchTeachersWizard(models.TransientModel):
    _name = "academy.timesheets.search.teachers.wizard"
    _description = "Academy timesheets search teachers wizard"

    _inherit = ["facility.scheduler.mixin"]

    _rec_name = "id"
    _order = "id DESC"

    def _search_for_teachers(self):
        time_start = 0.0 if self.full_day else self.time_start
        time_stop = 24.0 if self.full_day else self.time_stop

        dt = self.date_base
        date_start = self.join_datetime(dt, time_start, day_limit=True)
        date_stop = self.join_datetime(dt, time_stop, day_limit=True)

        date_start = date_start.strftime("%Y-%m-%d %H:%M:%S")
        date_stop = date_stop.strftime("%Y-%m-%d %H:%M:%S")

        session_domain = AND(
            [
                [("date_start", ">=", date_start)],
                [("date_start", "<", date_stop)],
                [("state", "=", "ready")],
            ]
        )
        session_obj = self.env["academy.training.session"]
        session_set = session_obj.search(session_domain)

        path = "teacher_assignment_ids.teacher_id.id"
        teacher_ids = session_set.mapped(path)

        teacher_domain = [("id", "not in", teacher_ids)]
        teacher_obj = self.env["academy.teacher"]
        teacher_set = teacher_obj.search(teacher_domain)

        return teacher_set

    def view_teachers(self):
        self.ensure_one()

        action_xid = "academy_base.action_teacher_act_window"
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update(self.as_context_default())

        teacher_set = self._search_for_teachers()

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": action.res_model,
            "target": "main",
            "name": self.env._("Teachers that match the criteria"),
            "view_mode": action.view_mode,
            "domain": [("id", "in", teacher_set.mapped("id"))],
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized
