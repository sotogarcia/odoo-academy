# -*- coding: utf-8 -*-
""" AcademyTrainingResourceKind

This module contains the academy.action.resource.kind Odoo model which stores
all training resource kind attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingResourceKind(models.Model):
    """This model allow user to sort out stored resources"""

    _name = "academy.training.resource.kind"
    _description = "Academy training resource kind"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=50,
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

    resource_ids = fields.One2many(
        string="Tests",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.resource",
        inverse_name="kind_id",
        domain=[],
        context={},
        auto_join=False,
    )
