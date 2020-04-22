# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.topic an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the real question topic

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestsTopic(models.Model):
    """ Topics are used to group serveral categories. IE, a topic named
    Internet could group the following categories: web pages, email, etc.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.topic'
    _description = u'Academy tests, question topic'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name for this topic",
        size=255,
        translate=True,
        track_visibility='onchange'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this test',
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

    category_ids = fields.One2many(
        string='Categories',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Allowed categories for questions in this topic',
        comodel_name='academy.tests.category',
        inverse_name='topic_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        # oldname='academy_category_ids'
    )


    # -------------------------- MANAGEMENT FIELDS ----------------------------

    category_count = fields.Integer(
        string='Number of categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of categories',
        compute=lambda self: self.compute_category_count()
    )

    # @api.multi
    @api.depends('category_ids')
    def compute_category_count(self):
        """ Computes `category_count` field value, this will be the number
        of categories related with this topic
        """
        for record in self:
            record.category_count = len(record.category_ids)


    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'category_uniq',
            'UNIQUE(name)',
            _(u'There is already another topic with the same name')
        )
    ]


