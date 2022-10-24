# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingHiringType(models.Model):
    """ Type of hiring.

    This can be: Career civil servants, Interim civil servants,
    Contracted staff, Temporary staff, Executive staff.
    """

    _name = 'academy.public.tendering.hiring.type'
    _description = u'Public tendering, hiring type of public employee'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this class',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this class',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you '
              'to hide record without removing it.')
    )

    _sql_constraints = [
        (
            'unique_name',
            'UNIQUE("name")',
            _('Another record with the same name already exists')
        )
    ]
