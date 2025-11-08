# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

from logging import getLogger


_logger = getLogger(__name__)


class AcademyStudentSignup(models.Model):
    """Per-company sign-up data for students."""

    _name = "academy.student.signup"
    _description = "Per-company sign-up data for academy students"

    _rec_name = "id"
    _order = "company_id, id"

    _check_company_auto = True

    company_id = fields.Many2one(
        string="Company",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help="Company this sign-up data applies to.",
        comodel_name="res.company",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    student_id = fields.Many2one(
        string="Student",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Student this sign-up data belongs to.",
        comodel_name="academy.student",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    signup_code = fields.Char(
        string="Sign-up code",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self._next_signup_code(self.env.company.id),
        help="Unique code assigned when the student signs up at the centre.",
        size=50,
        translate=False,
    )

    signup_date = fields.Datetime(
        string="Sign-up date",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: fields.Datetime.now(),
        help="Date and time when the student signed up at the centre.",
    )

    # -- Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            "unique_student_company",
            "UNIQUE(student_id, company_id)",
            "There is already sign-up data for this student and company.",
        ),
        (
            "uniq_code_company",
            "UNIQUE(company_id, signup_code)",
            "Sign-up code must be unique per company.",
        ),
    ]

    # -- Signup sequence methods
    # -------------------------------------------------------------------------

    @api.model
    def _ensure_signup_date(self, vals_list):
        today = fields.Datetime.now()
        for values in vals_list:
            if not values.get("signup_date"):
                values["signup_date"] = today

    @api.model
    def _next_signup_code(self, company_id):
        """Return next sign-up code using company-specific sequence,
        falling back to a known default XMLID."""
        sequence_obj = self.env["ir.sequence"].with_company(company_id)

        # 1) Try company-specific sequence (same code, bound to company)
        signup_code = "academy.student.signup.sequence"
        sequence_domain = [
            ("code", "=", signup_code),
            ("company_id", "=", company_id),
        ]
        sequence = sequence_obj.search(sequence_domain, limit=1)
        if sequence:
            return sequence.with_company(company_id).next_by_id()

        # 2) Explicit fallback to the known default sequence XMLID
        sequence_xid = "academy_base.ir_sequence_academy_student_signup"
        fallback = self.env.ref(sequence_xid, raise_if_not_found=False)
        if fallback:
            return fallback.with_company(company_id).next_by_id()

        # 3) Last resort: let Odoo try any global sequence with that code
        code = sequence_obj.next_by_code(signup_code)
        if code:
            _logger.warning(
                "Using global sequence by code for company_id=%s", company_id
            )
            return code

        raise UserError(
            _(
                "Missing sequence for student sign-up. "
                "Create a company-specific sequence with code %(code)s "
                "or define the fallback %(xid)s."
            )
            % {
                "code": signup_code,
                "xid": sequence_xid,
            }
        )

    @api.model
    def _ensure_signup_data(self, values):
        if not values.get("signup_code"):
            company_id = values.get("company_id") or self.env.company.id
            values["signup_code"] = self._next_signup_code(company_id)

        if not values.get("signup_date", False):
            values["signup_date"] = fields.Datetime.now()

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        for values in values_list:
            self._ensure_signup_data(values)

        result = super().create(values_list)

        return result
