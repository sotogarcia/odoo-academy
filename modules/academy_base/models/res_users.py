# -*- coding: utf-8 -*-
""" ResUsers

This module extend res.users model to link to own training resources
"""

from odoo import models, fields
from odoo.osv.expression import (
    TRUE_DOMAIN,
    FALSE_DOMAIN,
    NEGATIVE_TERM_OPERATORS,
)


from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class ResUsers(models.Model):
    """This model extends bae.model_res_users"""

    _name = "res.users"
    _inherit = ["res.users"]

    training_resource_ids = fields.One2many(
        string="Training resources",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose the training resources which he/she must update",
        comodel_name="academy.training.resource",
        inverse_name="updater_id",
        domain=[],
        context={},
        auto_join=False,
    )
