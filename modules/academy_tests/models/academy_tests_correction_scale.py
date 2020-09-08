# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsCorrectionScale(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

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
        digits=(16, 2),
        help='Score by right question'
    )

    wrong = fields.Float(
        string='Wrong',
        required=True,
        readonly=False,
        index=False,
        default=-1.0,
        digits=(16, 2),
        help='Score by wrong question'
    )

    blank = fields.Float(
        string='Blank',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Score by blank question'
    )
