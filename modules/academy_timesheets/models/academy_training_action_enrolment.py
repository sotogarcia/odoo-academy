# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module contains the academy.training.action.enrolment Odoo model which
stores all training action enrolment attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import AND, FALSE_DOMAIN, TRUE_DOMAIN
from odoo.addons.academy_base.utils.helpers import (
    OPERATOR_MAP,
    one2many_count,
    many2many_count,
)

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionEnrolment(models.Model):
    """Automatriculate students"""

    _inherit = ["academy.training.action.enrolment"]

    session_ids = fields.Many2manyView(
        string="Sessions",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="All sessions given to this enrolment",
        comodel_name="academy.training.session",
        relation="academy_training_session_invitation",
        column1="enrolment_id",
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

    invitation_ids = fields.One2many(
        string="Invitation",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="List of current invitations for the enrolment",
        comodel_name="academy.training.session.invitation",
        inverse_name="enrolment_id",
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

    # -- Overriden methods
    # -------------------------------------------------------------------------

    def write(self, values):
        """Overridden method 'write'"""

        major_changes = self._will_be_drastically_changed(values)
        if major_changes:
            values["invitation_ids"] = [(5, None, None)]

        parent = super(AcademyTrainingActionEnrolment, self)
        result = parent.write(values)

        return result

    # -- Public methods
    # -------------------------------------------------------------------------

    def view_invitations(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_invitation_act_window"
        action = self.env.ref(action_xid)

        ctx = {"default_enrolment_id": self.id}
        domain = [("enrolment_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.training.session.invitation",
            "target": "current",
            "name": self.env._("Invitations"),
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _will_be_drastically_changed(values):
        """If the student or the training action are changed, it means that
        the enrolment was wrong and that it is being replaced by a new one.

        Args:
            values (dict): write ``values`` dictionary

        Returns:
            bool: True if student or training action are in values
        """

        return "student_id" in values or "training_action_id" in values

    @staticmethod
    def _pick_up_dates(values):
        register = values.get("register", False)
        if register:
            register = fields.Datetime.from_string(register)

        deregister = values.get("deregister", False)
        if deregister:
            deregister = fields.Datetime.from_string(deregister)

        return register, deregister

    def _unlink_expired_invitations(self, values):
        unlink_set = self.env["academy.training.session.invitation"]

        invitation_set = self.mapped("invitation_ids")
        register, deregister = self._pick_up_dates(values)

        if register:
            unlink_set += invitation_set.filtered(
                lambda x: x.date_stop <= register
            )

        if deregister:
            unlink_set += invitation_set.filtered(
                lambda x: x.date_start >= deregister
            )

        unlink_set.unlink()

    def _link_pendent_invitations(self):
        raise NotImplementedError(
            "Method_link_pendent_invitations is not implemented yet"
        )
