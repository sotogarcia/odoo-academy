# -*- coding: utf-8 -*-
""" AcademyApplicationScope

This module contains the academy.application.scope Odoo model which stores
all application scope attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyApplicationScope(models.Model):
    """Application scope is a property of the training action"""

    _name = "academy.application.scope"
    _description = "Academy application scope"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new name",
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
        help="Enables/disables the record",
    )
