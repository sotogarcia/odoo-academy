# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.osv.expression import TRUE_DOMAIN

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

    session_count = fields.Integer(
        string="Session count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of related sessions",
        compute="_compute_session_count",
    )

    @api.depends("session_ids")
    def _compute_session_count(self):
        for record in self:
            target = record.session_ids.filtered(
                lambda x: x.date_stop >= fields.Datetime.now()
            )
            record.session_count = len(target)

    available_sessions_ids = fields.Many2manyView(
        string="Available sessions",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Sessions to which this student can be invited",
        comodel_name="academy.training.session",
        relation="academy_training_session_available_student_rel",
        column1="student_id",
        column2="session_id",
        domain=[],
        context={},
    )

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
        for record in self:
            record.invitation_count = len(record.invitation_ids)

    @api.model
    def _search_invitation_count(self, operator, value):
        return TRUE_DOMAIN

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

    def view_invitation(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_invitation_act_window"
        action = self.env.ref(action_xid)

        name = _("Invitation list of {}").format(self.name)

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
