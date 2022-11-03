# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceRecruitmentEmploymentGroup(models.Model):
    """ Group of public administration corps that require a similar degree
    """

    _name = 'civil.service.recruitment.employment.group'
    _description = u'Civil service recruitment, employment group of vacancy'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this group',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this group',
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
