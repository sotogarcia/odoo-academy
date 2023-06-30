# -*- coding: utf-8 -*-
""" AcademyTestsCorrectionScale

This module contains the academy.tests.correction.scale Odoo model which stores
all academy tests correction scale attributes and behavior.
"""

from odoo import models, fields
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsCorrectionScale(models.Model):
    """ This is a property of the academy.tests.test model
    """

    _name = 'academy.tests.correction.scale'
    _description = u'Academy tests correction scale'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Text for this answer',
        size=1024,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this topic',
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

    right = fields.Float(
        string='Right',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        digits=(16, 10),
        help='Score by right question'
    )

    wrong = fields.Float(
        string='Wrong',
        required=True,
        readonly=False,
        index=False,
        default=-1.0,
        digits=(16, 10),
        help='Score by wrong question'
    )

    blank = fields.Float(
        string='Blank',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 10),
        help='Score by blank question'
    )
