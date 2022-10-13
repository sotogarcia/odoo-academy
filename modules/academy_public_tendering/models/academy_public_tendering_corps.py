# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingVacancyPositionCorps(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.public.tendering.corps'
    _description = u'Academy public tendering corps'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Vacancy position type name",
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Something about this vacancy position type",
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

    employment_group_id = fields.Many2one(
        string='Employment group',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose employment group to which this record belongs',
        comodel_name='academy.public.tendering.employment.group',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    specialization_id = fields.Many2one(
        string='Specialization',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the required specialization',
        comodel_name='academy.public.tendering.required.specialization',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
