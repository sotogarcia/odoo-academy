# -*- coding: utf-8 -*-
""" AcademyTeacher

This module contains the academy.teacher Odoo model which stores
all teacher attributes and behavior.
"""

from odoo import models, fields
from odoo.tools import safe_eval
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTeacher(models.Model):
    """A teacher is a partner who can be enroled on training actions"""

    _name = "academy.teacher"
    _description = "Academy teacher"

    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "academy.member.mixin",
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

    training_unit_ids = fields.Many2many(
        string="Training units",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related training units",
        comodel_name="academy.training.module",
        relation="academy_training_module_teacher_rel",
        column1="teacher_id",
        column2="training_module_id",
        domain=[
            "|",
            ("training_module_id", "=", False),
            ("training_unit_ids", "=", False),
        ],
        context={},
    )
