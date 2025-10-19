# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import OR
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN

from operator import eq, ne, gt, ge, lt, le
from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import INCLUDE_ARCHIVED_DOMAIN, ARCHIVED_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from logging import getLogger
from datetime import datetime, date, time, timedelta


_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """A student is a partner who can be enroled on training actions"""

    _name = "academy.student"
    _description = "Academy student"

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

    enrolment_ids = fields.One2many(
        string="Student enrolments",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="All enrolments: past, current and future",
        comodel_name="academy.training.action.enrolment",
        inverse_name="student_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -- Computed field: enrolment_count --------------------------------------

    enrolment_count = fields.Integer(
        string="Nº enrolments",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Total number of enrolments",
        compute="_compute_enrolment_count",
        search="_search_enrolment_count",
    )

    @api.depends("enrolment_ids")
    def _compute_enrolment_count(self):
        counts = one2many_count(self, "enrolment_ids")

        for record in self:
            record.enrolment_count = counts.get(record.id, 0)

    @api.model
    def _search_enrolment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "enrolment_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    current_enrolment_ids = fields.One2many(
        string="Current enrolments",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Enrolments active at the current date/time",
        comodel_name="academy.training.action.enrolment",
        inverse_name="student_id",
        domain=[
            "&",
            ("register", "<=", fields.Datetime.now()),
            "|",
            ("deregister", "=", False),
            ("deregister", ">", fields.Datetime.now()),
        ],
        context={},
        auto_join=False,
    )

    # -- Computed field: last_deregister --------------------------------------

    last_deregister = fields.Datetime(
        string="End of training",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="End date of the most recent enrolment; 9999-12-31 if open.",
        compute="_compute_last_deregister",
    )

    @api.depends(
        "enrolment_ids",
        "enrolment_ids.deregister",
        "enrolment_ids.active",
    )
    @api.depends_context("allowed_company_ids", "force_company")
    def _compute_last_deregister(self):
        self.ensure_one()

        context = self.env.context.copy()
        context.update(active_test=False)

        enrolment_obj = self.env["academy.training.action.enrolment"]
        enrolment_obj = enrolment_obj.with_context(context).sudo()

        now = fields.Datetime.now()
        infinity = datetime.max

        domain = [
            "&",
            "&",
            ("student_id", "in", self.ids),
            ("company_id", "=", self.env.company.id),
            "|",
            ("available_until", "<=", now),
            ("active", "=", True),
        ]
        rows = enrolment_obj.read_group(
            domain=domain,
            fields=["available_until:max"],
            groupby=["student_id"],
            lazy=False,
        )

        last_out = {r["student_id"][0]: r.get("available_until") for r in rows}

        for record in self:
            if record.id not in last_out:
                record.last_deregister = None
            else:
                record.last_deregister = last_out.get(record.id, infinity)

    def _search_last_deregister(self, operator, value):
        """Search students by the deregister date of their most recent
        enrolment within the active company.
        """

        # Ensure the context ignores active_test, to include all enrolments
        context = dict(self.env.context, active_test=False)

        enrolment_obj = (
            self.env["academy.training.action.enrolment"]
            .with_context(context)
            .sudo()
        )

        # Group by student_id and get the latest deregister date per company
        rows = enrolment_obj.read_group(
            domain=[("company_id", "=", self.env.company.id)],
            fields=["deregister:max"],
            groupby=["student_id"],
            lazy=False,
        )

        # Build dict: {student_id: last_deregister}
        last_out = {r["student_id"][0]: r.get("deregister") for r in rows}

        # Map Odoo operators to Python comparison functions
        pycmp = {
            "=": eq,
            "==": eq,
            "!=": ne,
            "<>": ne,
            ">": gt,
            "<": lt,
            ">=": ge,
            "<=": le,
        }

        compare = pycmp.get(operator)
        if not compare:
            # Return empty domain for unsupported operators
            return [("id", "in", [])]

        matched_ids = [
            sid for sid, dt in last_out.items() if dt and compare(dt, value)
        ]

        return [("id", "in", matched_ids)]

    # -- Computed field: current_enrolment_count ------------------------------

    current_enrolment_count = fields.Integer(
        string="Nº current enrolments",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of currently active enrolments",
        compute="_compute_current_enrolment_count",
        search="_search_current_enrolment_count",
    )

    @api.depends(
        "current_enrolment_ids",
        "enrolment_ids.register",
        "enrolment_ids.deregister",
    )
    def _compute_current_enrolment_count(self):
        counts = one2many_count(self, "current_enrolment_ids")

        for record in self:
            record.current_enrolment_count = counts.get(record.id, 0)

    @api.model
    def _search_current_enrolment_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "current_enrolment_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -- Computed field: enrolment_str ----------------------------------------

    enrolment_str = fields.Char(
        string="Enrolment summary",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Current over total enrolments (e.g., “2 / 5”)",
        size=6,
        translate=False,
        compute="_compute_enrolment_str",
    )

    @api.depends(
        "enrolment_ids",
        "current_enrolment_ids",
        "enrolment_count",
        "current_enrolment_count",
    )
    def _compute_enrolment_str(self):
        for record in self:
            current = record.current_enrolment_count or 0
            total = record.enrolment_count or 0

            if total == 0 or current == total:
                record.enrolment_str = str(total)
            else:
                record.enrolment_str = "{} / {}".format(current, total)

    # -- Methods overrides -------------------------------------------

    @api.model
    def _get_relevant_category_external_id(self):
        return "academy_base.res_partner_category_student"

    @api.model
    def _get_relevant_signup_sequence_code(self):
        return "academy.student.signup.sequence"

    @api.model
    def _get_relevant_signup_sequence_external_id(self):
        return "academy_base.ir_sequence_academy_student_signup"

    # -- Public methods -------------------------------------------------------

    def view_enrolments(self):
        self.ensure_one()

        name = self.env._("Enrolments: {}").format(self.display_name)

        act_xid = "{module}.{name}".format(
            module="academy_base",
            name="action_training_action_enrolment_act_window",
        )
        action = self.env.ref(act_xid)

        view_xid = "{module}.{name}".format(
            module="academy_base",
            name="view_academy_training_action_enrolment_edit_by_user_tree",
        )

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.domain or "[]", {"uid": self.env.uid}))
        ctx.update({"default_student_id": self.id})
        ctx.update({"list_view_ref": view_xid})

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [("student_id", "=", self.id)]])

        action_values = {
            "name": name,
            "type": action.type,
            "help": action.help,
            "domain": domain,
            "context": ctx,
            "res_model": action.res_model,
            "target": action.target,  # "current",
            "view_mode": action.view_mode,
            "search_view_id": action.search_view_id.id,
            "nodestroy": True,
        }

        return action_values

    def fetch_enrolled(
        self, training_actions=None, point_in_time=None, archived=False
    ):
        student_set = self.env["academy.student"]

        domains = []

        if self:
            domain = create_domain_for_ids("student_id", self)
            domains.append(domain)

        if training_actions:
            domain = create_domain_for_ids(
                "training_action_id", training_actions
            )
            domains.append(domain)

        if point_in_time:
            domain = create_domain_for_interval(
                "register", "deregister", point_in_time
            )
            domains.append(domain)

        if archived is None:
            domains.append(INCLUDE_ARCHIVED_DOMAIN)
        elif archived is True:
            domains.append(ARCHIVED_DOMAIN)

        if domains:
            enrolment_obj = self.env["academy.training.action.enrolment"]
            enrolment_set = enrolment_obj.search(AND(domains))
            student_set = enrolment_set.mapped("student_id")

        return student_set
