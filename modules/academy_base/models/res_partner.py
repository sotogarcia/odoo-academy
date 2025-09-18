# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from stdnum.util import ValidationError
from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.exceptions import UserError
from odoo.osv.expression import AND, OR

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
        help="Show related student",
        comodel_name="academy.student",
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
    )

    @api.depends("student_id")
    def _compute_is_student(self):
        for record in self:
            record.is_student = bool(record.student_id)

    def _search_is_student(self, operator, value):
        operator = self._check_operator(operator)

        if value:
            operator = "!=" if operator == "=" else "="
            value = not value

        return [("student_id", operator, value)]

    # -- Constraints ----------------------------------------------------------

    @api.constrains("ref", "vat", "email")
    def _check_unique_partner(self):
        if self.env.context.get("skip_partner_unique_check"):
            return

        for record in self:
            if not record.student_id:
                continue

            self._validate_unique_partner_identifiers(record)

    # -- Standard methods overrides -------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Sanitize key fields before creating partner records.

        Works with multi-create (list of dicts) and single dict (legacy).
        """
        vals_list = self._sanitize_indexing_values(vals_list)
        return super().create(vals_list)

    def write(self, values):
        """Sanitize key fields before updating partner records.

        Applies to all records in the current recordset.
        """
        values = self._sanitize_indexing_values(values)
        return super().write(values)

    # -- Sanitize some relevant fields-----------------------------------------

    @api.model
    def _validate_unique_partner_identifiers(self, partner):
        partner_obj = self.env["res.partner"].with_context(active_test=False)
        message = _("Contact with the same %s (%s) already exists")

        # Apply only to partners linked to at least one student
        if not partner.student_id:
            return

        # Build an OR of exact, case-insensitive matches for provided keys.
        # This constraint runs on res.partner, so we exclude partner.id.
        leafs = []
        for key in ["ref", "vat", "email"]:
            value = getattr(partner, key, False)
            if isinstance(value, str):
                value = value.strip()
            if value:
                leafs.append([(key, "=ilike", value)])

        # Nothing to validate if no identifiers present
        if not leafs:
            return

        # Fast duplicate check (any field collides), excluding self
        domain = AND(
            [
                [("id", "!=", partner.id), ("student_id", "!=", False)],
                OR(leafs),
            ]
        )
        if partner_obj.search_count(domain) == 0:
            return

        # Duplicates found: identify the culprit field to report it
        for key in ["ref", "vat", "email"]:
            value = getattr(partner, key, False)
            if isinstance(value, str):
                value = value.strip()
            if not value:
                continue

            # Pinpoint which field collides to craft a precise message
            domain = [
                "&",
                "&",
                ("id", "!=", partner.id),
                ("student_id", "!=", False),
                (key, "=ilike", value),
            ]
            if partner_obj.search_count(domain):
                raise ValidationError(message % (key, value))

    @staticmethod
    def _sanitize_indexing_values(value_list):
        """Normalize partner indexing fields before storing.

        Accepts a dict (single record) or a list/tuple of dicts (multi).
        Operates in place and returns the same container.

        Rules:
        - ref: strip
        - vat: strip + upper
        - email: strip + lower
        - Empty result: remove key
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
                if not value:
                    values.pop(key)
                    continue

                if operation:
                    value = getattr(value, operation)()

                values[key] = value

        return value_list

    # -- Auxiliary methods ----------------------------------------------------

    @staticmethod
    def _check_operator(operator):
        if operator in ["is", "="]:
            return "="
        elif operator in ["not is", "not is", "!=", "<>"]:
            return "!="
        else:
            raise UserError("Operator not supported")

    def _avoid_double_unique_check(self, values):
        keys = {"ref", "vat", "email"}
        value_list = values if isinstance(values, (list, tuple)) else [values]
        touching_ids = any(any(k in vals for k in keys) for vals in value_list)
        if touching_ids:
            return super()

        context = self.env.context.copy()
        context.update(skip_partner_unique_check=True)
        return super().with_context(context)

    @api.model_create_multi
    def create(self, vals_list):
        """Create students; avoid double unique-check when not touching IDs."""
        keys = {"ref", "vat", "email"}
        seq = (
            vals_list if isinstance(vals_list, (list, tuple)) else [vals_list]
        )
        touching_ids = any(any(k in vals for k in keys) for vals in seq)
        if touching_ids:
            return super().create(vals_list)
        return (
            super()
            .with_context(skip_partner_unique_check=True)
            .create(vals_list)
        )

    def write(self, vals):
        """Write students; avoid double unique-check when not touching IDs."""
        if any(k in vals for k in ("ref", "vat", "email")):
            return super().write(vals)
        return super().with_context(skip_partner_unique_check=True).write(vals)
