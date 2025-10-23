# -*- coding: utf-8 -*-
""" AcademyTeacher

This module contains the academy.teacher Odoo model which stores
all teacher attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTeacher(models.Model):
    """A teacher is a partner who can be enroled on training actions"""

    _name = "academy.teacher"
    _description = "Academy teacher"

    _inherit = [
        "academy.support.staff",
    ]

    _order = "complete_name ASC, id DESC"

    _rec_name = "complete_name"
    _rec_names_search = [
        "complete_name",
        "email",
        "signup_code",
        "vat",
        "company_registry",
    ]

    assignment_ids = fields.One2many(
        string="Assignments",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Training actions or actions lines assigned to this teacher.",
        comodel_name="academy.training.teacher.assignment",
        inverse_name="teacher_id",
        domain=[],
        context={},
        auto_join=False,
    )

    assignment_count = fields.Integer(
        string="No. of teachers",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_assignment_count",
        search="_search_assignment_count",
    )

    @api.depends("assignment_ids")
    def _compute_assignment_count(self):
        counts = one2many_count(self, "assignment_ids")

        for record in self:
            record.assignment_count = counts.get(record.id, 0)

    @api.model
    def _search_assignment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "assignment_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Methods overrides ----------------------------------------------------

    @api.model
    def _get_relevant_category_external_id(self):
        return "academy_base.res_partner_category_teacher"

    @api.model
    def _get_relevant_signup_sequence_code(self):
        return "academy.teacher.signup.sequence"

    @api.model
    def _get_relevant_signup_sequence_external_id(self):
        return "academy_base.ir_sequence_academy_teacher_signup"

    # -- Public methods -------------------------------------------------------

    def view_assignments(self):
        self.ensure_one()

        action_xid = "academy_base.action_teacher_assignment_act_window"
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Assignments: {}").format(self.display_name)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_teacher_id": self.id})

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
