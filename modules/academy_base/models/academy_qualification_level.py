# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyQualificationLevel(models.Model):
    """ Set of qualifications according to criteria of the complexity of
    task.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.qualification.level'
    _description = u'Academy qualification level'

    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
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

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Choose level order'
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )
