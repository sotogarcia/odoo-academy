# -*- coding: utf-8 -*-
""" AcademyTeacher

This module contains the academy.technical.staff Odoo model which stores
all technical staff members attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTeacher(models.Model):
    """A technical staff is a partner who can be enroled on training actions"""

    _name = "academy.technical.staff"
    _description = "Academy technical staff member"

    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "academy.support.staff",
    ]

    _order = "complete_name ASC, id DESC"

    _rec_name = "complete_name"
    _rec_names_search = [
        "complete_name",
        "email",
        "ref",
        "vat",
        "company_registry",
    ]

    # -- Methods overrides ----------------------------------------------------

    @api.model
    def _get_relevant_category_external_id(self):
        return "academy_base.res_partner_category_technical_staff"

    @api.model
    def _get_relevant_signup_sequence_code(self):
        return "academy.technical.staff.signup.sequence"

    @api.model
    def _get_relevant_signup_sequence_external_id(self):
        return "academy_base.ir_sequence_academy_technical_staff_signup"
