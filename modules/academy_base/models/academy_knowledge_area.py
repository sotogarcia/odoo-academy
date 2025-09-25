# -*- coding: utf-8 -*-
""" AcademyKnowledgeArea

This module contains the academy.knowledge.area Odoo model which stores
all Knowledge Area attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyKnowledgeArea(models.Model):
    """Knowledge area is a property of the training action"""

    _name = "academy.knowledge.area"
    _description = "Academy knowledge area"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new description",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
    )

    knowle_code = fields.Char(
        string="Code",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new code",
        size=30,
        translate=False,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new description",
        translate=True,
    )
