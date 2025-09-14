# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.exceptions import UserError

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
        inverse_name="res_partner_id",
        domain=[],
        context={},
        auto_join=False,
    )

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

    @staticmethod
    def _check_operator(operator):
        if operator in ["is", "="]:
            return "="
        elif operator in ["not is", "not is", "!=", "<>"]:
            return "!="
        else:
            raise UserError("Operator not supported")

    def _search_is_student(self, operator, value):
        operator = self._check_operator(operator)

        if value:
            operator = "!=" if operator == "=" else "="
            value = not value

        return [("student_id", operator, value)]

    def go_to_student(self):
        self.ensure_one()

        return {
            "name": self.student_id.name,
            "view_mode": "form",
            "view_id": False,
            "view_type": "form",
            "res_model": "academy.student",
            "res_id": self.student_id.id,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "main",
        }

    def convert_to_student(self):
        """Convert partner in student"""

        student_set = self.env["academy.student"]

        for record in self:
            if not record.student_id:
                values = {"res_partner_id": record.id}
                record.student_id = student_set.create(values)
                record._log_convert_to_student_result(exists=False)

            else:
                record._log_convert_to_student_result(exists=True)

            student_set += record.student_id

        return student_set

    def _log_convert_to_student_result(self, exists):
        self.ensure_one()

        if exists:
            msg = _("Student {} already exists for partner {}.").format(
                self.student_id.id, self.id
            )
            _logger.warning(msg)

        else:
            msg = _("New student {} created for partner {}.").format(
                self.student_id.id, self.id
            )

            _logger.debug(msg)
