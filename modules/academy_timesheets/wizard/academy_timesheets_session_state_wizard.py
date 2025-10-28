# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTimesheetsSessionStateWizard(models.TransientModel):
    """Wizard to change the state to several sessions at the same time"""

    _name = "academy.timesheets.session.state.wizard"
    _description = "Academy timesheet session state wizard"

    _rec_name = "id"
    _order = "id ASC"

    session_ids = fields.Many2many(
        string="Sessions",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_session_ids(),
        help="Target sessions",
        comodel_name="academy.training.session",
        relation="academy_timesheets_session_state_wizard_rel",
        column1="wizard_id",
        column2="session_id",
        domain=[],
        context={},
    )

    state = fields.Selection(
        string="State",
        required=True,
        readonly=False,
        index=False,
        default="ready",
        help="Choose new session status",
        selection=[("draft", "Draft"), ("ready", "Ready")],
    )

    session_count = fields.Integer(
        string="Session count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Total number of sessions",
    )

    draft_session_count = fields.Integer(
        string="In draft",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions in Draft state",
        compute="_compute_draft_session_count",
    )

    @api.depends("session_ids")
    def _compute_draft_session_count(self):
        for record in self:
            draft_session_set = record.session_ids.filtered(
                lambda r: r.state == "draft"
            )
            record.draft_session_count = len(draft_session_set)

    ready_count = fields.Integer(
        string="In ready",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions in Ready state",
        compute="_compute_ready_count",
    )

    @api.depends("session_ids")
    def _compute_ready_count(self):
        for record in self:
            ready_session_set = record.session_ids.filtered(
                lambda r: r.state == "ready"
            )
            record.ready_count = len(ready_session_set)

    target_count = fields.Integer(
        string="Targets",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions to which the status will be changed",
        compute="_compute_target_count",
    )

    @api.depends("session_ids", "state", "force_all")
    def _compute_target_count(self):
        for record in self:
            target_session_set = record.session_ids
            if not record.force_all:
                target_session_set = target_session_set.filtered(
                    lambda r: r.state != record.state
                )
            record.target_count = len(target_session_set)

    mail_create_nosubscribe = fields.Boolean(
        string="No subscribe",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Check it to add mail_create_nosubscribe key in context",
    )

    skip_email_notification = fields.Boolean(
        string="Skip email",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=(
            "Check it to post messages in chatter only. No email "
            "notification will be sent."
        ),
    )

    invite_those_enrolled = fields.Boolean(
        string="Invite those enrolled",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Check it to invite those enrolled ",
    )

    force_all = fields.Boolean(
        string="Force all",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Check it to update all records even if they don't need it",
    )

    def default_session_ids(self):
        session_set = self.env["academy.training.session"]

        active_model = self.env.context.get("active_model", None)
        if active_model == "academy.training.session":
            active_ids = self.env.context.get("active_ids", [])
            if not active_ids:
                active_id = self.env.context("active_id", False)
                if active_id:
                    active_ids = [active_id]

            if active_ids:
                session_domain = [("id", "in", active_ids)]
                session_set = session_set.search(session_domain)

        return session_set

    @api.onchange("session_ids")
    def _onchange_session_id(self):
        for record in self:
            states = record.mapped("session_ids.state")
            record.session_count = len(states)

            in_draft = [item for item in states if item == "draft"]
            in_ready = [item for item in states if item == "ready"]

            if len(in_ready) > len(in_draft):
                record.state = "draft"
            else:
                record.state = "ready"

    def perform_action(self):
        self.ensure_one()

        context = self.env.context.copy()
        context.update(
            {
                "mail_create_nosubscribe": self.mail_create_nosubscribe,
                "skip_email_notification": self.skip_email_notification,
            }
        )

        session_set = self.session_ids.with_context(context)
        if not self.force_all:
            session_set = session_set.filtered(lambda r: r.state != self.state)

        if self.invite_those_enrolled:
            session_set.invite_all()

        session_set.write({"state": self.state})
