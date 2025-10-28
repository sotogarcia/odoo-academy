# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN
from odoo.addons.academy_base.utils.helpers import OPERATOR_MAP, one2many_count
from odoo.osv.expression import TERM_OPERATORS_NEGATION
from odoo.tools.safe_eval import safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionLine(models.Model):
    """Append fields to set teachers"""

    _inherit = ["academy.training.action.line"]

    session_ids = fields.One2many(
        string="Sessions",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="All sessions for program unit",
        comodel_name="academy.training.session",
        inverse_name="action_line_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -- session_count: field and logic ---------------------------------------

    session_count = fields.Integer(
        string="Session count",
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

    # -------------------------------------------------------------------------

    draft_session_ids = fields.One2many(
        string="Draft sessions",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="All sessions in draft state for training action",
        comodel_name="academy.training.session",
        inverse_name="action_line_id",
        domain=[("state", "=", "draft")],
        context={},
        auto_join=False,
    )

    # -- draft_session_count: field and logic ---------------------------------

    draft_session_count = fields.Integer(
        string="Draft count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions in draft state",
        compute="_compute_draft_session_count",
        search="search_draft_session_count",
    )

    @api.depends("draft_session_ids")
    def _compute_draft_session_count(self):
        counts = one2many_count(self, "draft_session_ids")

        for record in self:
            record.draft_session_count = counts.get(record.id, 0)

    @api.model
    def search_draft_session_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "draft_session_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Public methods
    # -------------------------------------------------------------------------

    def view_timesheets(self):
        action_xid = (
            "academy_timesheets."
            "action_academy_training_action_line_timesheet_act_window"
        )
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))

        if self:
            domain = [("action_line_id", "in", self.mapped("id"))]
        else:
            domain = TRUE_DOMAIN

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": action.res_model,
            "target": action.target,
            "name": action.name,
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized
