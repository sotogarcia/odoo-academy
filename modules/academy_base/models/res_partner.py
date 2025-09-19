# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError
from ..utils.sql_helpers import create_index


from logging import getLogger

_logger = getLogger(__name__)


class ResPartner(models.Model):
    """Partner can be converted to a student"""

    _inherit = "res.partner"

    student_id = fields.One2many(
        string="Student",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Show the single related ",
        comodel_name="academy.student",
        inverse_name="partner_id",
        domain=[],
        context={},
        auto_join=False,
    )

    teacher_id = fields.One2many(
        string="Teacher",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Show the single related teacher",
        comodel_name="academy.teacher",
        inverse_name="partner_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -- Computed field: is_student--------------------------------------------

    is_student = fields.Boolean(
        string="Is student",
        required=False,
        readonly=True,
        index=False,
        default=False,
        help="Check if partner is a student",
        compute="_compute_is_student",
        search="_search_is_student",
        store=True,
    )

    @api.depends("student_id")
    def _compute_is_student(self):
        for record in self:
            record.is_student = bool(
                record.with_context(active_test=False).student_id
            )

    def _search_is_student(self, operator, value):
        operator = self._check_operator(operator)

        if value:
            operator = "!=" if operator == "=" else "="
            value = not value

        return [("student_id", operator, bool(value))]

    # -- Computed field: is_teacher -------------------------------------------

    is_teacher = fields.Boolean(
        string="Is teacher",
        required=False,
        readonly=True,
        index=False,
        default=False,
        help="Check if partner is a teacher",
        compute="_compute_is_teacher",
        search="_search_is_teacher",
        store=True,
    )

    @api.depends("teacher_id")
    def _compute_is_teacher(self):
        for record in self:
            record.is_teacher = bool(
                record.with_context(active_test=False).teacher_id
            )

    def _search_is_teacher(self, operator, value):
        operator = self._check_operator(operator)

        if value:
            operator = "!=" if operator == "=" else "="
            value = not value

        return [("teacher_id", operator, bool(value))]

    # -- Expand the capabilities of the standard ORM model --------------------

    def init(self):
        """Create partial unique indexes for student and teacher partners
        in vat, ref and email.

        Enforces uniqueness only when is_student = TRUE or is_teacher = TRUE,
        matching the normalization rules used at ORM level.
        """
        teacher_or_student = "(is_teacher = TRUE or is_student = TRUE)"

        where_clause = f"{teacher_or_student} AND btrim(\"ref\") <> ''"
        create_index(
            self.env,
            "res_partner",
            "lower(btrim(ref))",
            unique=True,
            name="res_partner__ref_student_teacher_pindex",
            where=where_clause,
        )

        where_clause = f"{teacher_or_student} AND btrim(vat) <> ''"
        create_index(
            self.env,
            "res_partner",
            "upper(btrim(vat))",
            unique=True,
            name="res_partner__vat_student_teacher_pindex",
            where=where_clause,
        )

        where_clause = f"{teacher_or_student} AND btrim(email) <> ''"
        create_index(
            self.env,
            "res_partner",
            "lower(btrim(email))",
            unique=True,
            name="res_partner__email_student_teacher_pindex",
            where=where_clause,
        )

    # -- Standard methods overrides -------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Sanitize values (ref, vat, email) before creating partner records.

        Works with multi-create (list of dicts) and single dict (legacy).
        """
        vals_list = self._sanitize_indexing_values(vals_list)
        return super().create(vals_list)

    def write(self, values):
        """Sanitize values (ref, vat, email) before creating partner records.

        Applies to all records in the current recordset.
        """
        values = self._sanitize_indexing_values(values)
        return super().write(values)

    # -- Sanitize some relevant fields-----------------------------------------

    @staticmethod
    def _sanitize_indexing_values(value_list):
        """Normalize partner indexing fields before storing.

        Accepts a dict (single record) or a list/tuple of dicts (multi).
        Operates in place and returns the same container.

        Rules:
        - ref: strip
        - vat: strip + upper
        - email: strip + lower
        - If the value is empty `''`, set it to `None`
        """
        sanitize = dict(ref=None, vat="upper", email="lower")

        if not value_list:
            return value_list

        if isinstance(value_list, dict):
            target_list = [value_list]
        else:
            target_list = value_list

        for values in target_list:
            for key, operation in sanitize.items():
                if key not in values:
                    continue

                value = values.get(key, False)
                if not isinstance(value, str):
                    continue

                value = value.strip()
                if operation:
                    value = getattr(value, operation)()

                values[key] = value or None

        return value_list

    # -- Auxiliary methods ----------------------------------------------------

    @staticmethod
    def _check_operator(operator):
        op = (operator or "").strip().lower()
        if op in ["is", "="]:
            return "="
        elif op in ["not is", "is not", "!=", "<>"]:
            return "!="
        else:
            raise UserError(f"Operator not supported: {operator!r}")
