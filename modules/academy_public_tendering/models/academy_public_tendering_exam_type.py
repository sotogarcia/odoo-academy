# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingExamType(models.Model):
    """ Type of exam
    This can be: Open exam, Concourse, Concourse/Exam
    """

    _name = 'academy.public.tendering.exam.type'
    _description = u'Public tendering, kind of vacancy position'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this kind',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this kind',
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
