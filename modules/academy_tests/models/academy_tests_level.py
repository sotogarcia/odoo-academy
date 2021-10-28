# -*- coding: utf-8 -*-
""" AcademyTestsLevel

This module contains the academy.tests.level Odoo model which stores
all academy tests level attributes and behavior.
"""

from odoo import models, fields
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsLevel(models.Model):
    """ This is a property of the academy.tests.test model
    """

    _name = 'academy.tests.level'
    _description = u'Academy tests, question difficulty level'

    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this level',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this level',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it')
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help='Sequence order for difficulty'
    )

    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'level_uniq',
            'UNIQUE(name)',
            _(u'There is already another level with the same name')
        )
    ]
