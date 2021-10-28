# -*- coding: utf-8 -*-
""" AcademyTestsTestKind

This module contains the academy.tests.kind Odoo model which stores
all academy tests kind attributes and behavior.
"""
from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTestKind(models.Model):
    """ This is a property of the academy.tests.test model
    """

    _name = 'academy.tests.test.kind'
    _description = u'Academy tests test kind'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = ['image.mixin']

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    test_ids = fields.One2many(
        string='Used in tests',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        inverse_name='test_kind_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
