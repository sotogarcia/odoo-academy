# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN
from odoo.addons.academy_base.utils.helpers import (
    OPERATOR_MAP,
    one2many_count,
    many2many_count,
)

from logging import getLogger


_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """Button to open session calendar"""

    _inherit = ["academy.student"]

    session_ids = fields.Many2manyView(
        string="Sessions",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="All sessions given to this student",
        comodel_name="academy.training.session",
        relation="academy_training_session_invitation",
        column1="student_id",
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
        counts = many2many_count(self, "session_ids")

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

        counts = many2many_count(self.search([]), "session_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -------------------------------------------------------------------------

    available_sessions_ids = fields.Many2manyView(
        string="Available sessions",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Sessions to which this student can be invited",
        comodel_name="academy.training.session",
        relation="academy_training_session_invitation",
        column1="student_id",
        column2="session_id",
        domain=[],  # Todo: Esto no está bien y antes había una vista
        context={},
    )

    # -- available_session_count: field and logic -----------------------------

    available_session_count = fields.Integer(
        string="No. of available sessions",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions on which the calculation has been made",
        compute="_compute_available_session_count",
        search="search_available_session_count",
    )

    @api.depends("available_sessions_ids")
    def _compute_available_session_count(self):
        counts = many2many_count(self, "available_sessions_ids")

        for record in self:
            record.available_session_count = counts.get(record.id, 0)

    @api.model
    def search_available_session_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = many2many_count(self.search([]), "available_sessions_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -------------------------------------------------------------------------

    invitation_ids = fields.One2many(
        string="Invitation",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Invitation list for the student",
        comodel_name="academy.training.session.invitation",
        inverse_name="student_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -- intivation_count: field and logic ------------------------------------

    invitation_count = fields.Integer(
        string="Invitation count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions to which the student has been invited",
        compute="_compute_invitation_count",
        search="_search_invitation_count",
        store=False,
    )

    @api.depends("invitation_ids")
    def _compute_invitation_count(self):
        counts = one2many_count(self, "invitation_ids")

        for record in self:
            record.invitation_count = counts.get(record.id, 0)

    @api.model
    def _search_invitation_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "invitation_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Public methods
    # -------------------------------------------------------------------------

    def view_invitations(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_invitation_act_window"
        action = self.env.ref(action_xid)

        name = self.env._("Invitation list of {}").format(self.name)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({"default_student_id": self.id})

        domain = [("student_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.training.session.invitation",
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

    # -- Auxliliary methods
    # -------------------------------------------------------------------------

    def _compute_view_mapping(self):
        view_names = [
            "view_academy_training_session_invitation_calendar",
            "view_academy_training_session_invitation_tree",
            "view_academy_training_session_invitation_form",
        ]

        view_mapping = []
        for view_name in view_names:
            xid = "academy_timesheets.{}".format(view_name)
            view = self.env.ref(xid)
            pair = (view.id, view.type)
            view_mapping.append(pair)

        return view_mapping
