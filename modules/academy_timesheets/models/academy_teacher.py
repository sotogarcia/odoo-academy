# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import AND, FALSE_DOMAIN, TRUE_DOMAIN
from odoo.addons.academy_base.utils.helpers import OPERATOR_MAP, one2many_count

from logging import getLogger
from urllib.parse import urljoin


_logger = getLogger(__name__)


class AcademyTeacher(models.Model):
    """Button to open session calendar"""

    _inherit = ["academy.teacher"]

    session_ids = fields.Many2manyView(
        string="Sessions",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Sessions that this professor will participate in",
        comodel_name="academy.training.session",
        relation="academy_training_session_teacher_assignment",
        column1="teacher_id",
        column2="session_id",
        domain=[],
        context={},
    )

    # -- session_count: field and logic ---------------------------------------

    session_count = fields.Integer(
        string="No. of sessions",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions on which the calculation has been made",
        compute="_compute_session_count",
        search="search_session_count",
    )

    @api.depends("session_ids")
    def _compute_session_count(self):
        counts = one2many_count(self, "session_ids")

        for record in self:
            record.session_count = counts.get(record.id, 0)

    @api.model
    def search_session_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "session_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- schedule_url: field and logic ----------------------------------------

    schedule_url = fields.Char(
        string="Schedule URL",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Compute base report URL",
        size=2048,
        translate=False,
        compute="_compute_schedule_url",
    )

    def _compute_schedule_url(self):
        """This will be used in a email template. The URL will be always the
        same, but it must be gotten from ir.config_parameter.
        """
        config = self.env["ir.config_parameter"].sudo()
        base_url = config.get_param("web.base.url")
        url = urljoin(base_url, "/academy-timesheets/teacher/schedule")

        for record in self:
            record.schedule_url = url

    # -- Public methods
    # -------------------------------------------------------------------------

    def view_sessions(self, definitive=False, all_companies=True):
        """
        Generate an action to view sessions taught by the current teacher.

        This method prepares a context and domain for filtering sessions in
        the 'academy.training.session' model. It considers sessions where the
        current teacher is the primary teacher and applies additional filters
        based on the 'definitive' and 'all_companies' parameters.

        Args:
            definitive (bool, optional): If True, only sessions with a state of
            'ready' are included. Defaults to True.
            all_companies (bool, optional): If True, sessions from all
            companies are included. Otherwise, only sessions from the current
            company are considered. Defaults to True.

        Returns:
            dict: A dictionary representing an Odoo window action. This
            dictionary contains information like the view type, target model,
            domain, context, and view_mode required to display the sessions in
            the Odoo UI.
        """
        self.ensure_one()

        action_xid = "academy_timesheets.action_sessions_act_window"
        action = self.env.ref(action_xid)

        name = self.env._("Sessions taught by {}").format(self.name)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update(
            {
                "default_primary_teacher_id": self.id,
                "academy_timesheet_for_all_companies": all_companies,
            }
        )

        domain = [("teacher_ids", "=", self.id)]
        if definitive:
            ready_domain = [("state", "=", "ready")]
            domain = AND([domain, ready_domain])

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.training.session",
            "target": "current",
            "name": name,
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
            "views": self._compute_view_mapping(),
        }

        return serialized

    def view_operational_shifts(self):
        self.ensure_one()

        action_xid = (
            "academy_timesheets." "action_teacher_operational_shift_act_window"
        )
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Shifts")

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        domain = [("teacher_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def get_reference(self):
        """Required by clone wizard

        Returns:
            str: model,id
        """

        self.ensure_one()

        return "{},{}".format(self._name, self.id)

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def _compute_view_mapping(self):
        view_names = [
            "view_academy_training_session_calendar_no_primary_instructor",
            "view_academy_training_session_kanban",
            "view_academy_training_session_tree",
            "view_academy_training_session_pivot",
            "view_academy_training_session_form",
        ]

        view_mapping = []
        for view_name in view_names:
            xid = "academy_timesheets.{}".format(view_name)
            view = self.env.ref(xid)
            pair = (view.id, view.type)
            view_mapping.append(pair)

        return view_mapping
