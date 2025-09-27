# -*- coding: utf-8 -*-
""" AcademyTrainingMethodology

This module contains the academy.training.methodology Odoo model which stores
all training methodology attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingMethodology(models.Model):
    """Training methodology is a property of the training action"""

    _name = "academy.training.methodology"
    _description = "Academy training methodology"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Training Methodology",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Training Methodology",
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
