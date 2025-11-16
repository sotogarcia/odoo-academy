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
    """A technical staff is a partner who can be enrolled on training actions"""

    _name = "academy.technical.staff"
    _description = "Academy technical staff member"

    _inherit = [
        "academy.support.staff",
    ]

    _order = "complete_name ASC, id DESC"

    _rec_name = "complete_name"
    _rec_names_search = [
        "complete_name",
        "email",
        "vat",
        "company_registry",
    ]

    # -- Methods overrides ----------------------------------------------------

    @api.model
    def _get_relevant_category_external_id(self):
        return "academy_base.res_partner_category_technical_staff"
