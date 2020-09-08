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
import re

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


    @staticmethod
    def findall(regex, strlist):
        """ Search regex pattern in a list of strings. It's used to
        search pattern in question name and question description
        """
        result = False

        for stritem in strlist:
            result = regex.findall(stritem)
            if result:
                break

        return result


    def search_for_categories(self, _in_string):
        """ Search partial matches for all category keywords in given string
        and returns that categories

        Returned value wille be a dictionary {topic_id: [categorory_id1, ...]}
        """

        msg = _('Error on autocategorize. Text: {}, Keywords: {}, Error: {}')
        result = {}
        if isinstance(_in_string, str):
            _in_string = [_in_string]

        # STEP 1: Run over topic recordset
        for record in self:

            result[record.id] = []
            cat_items = record.category_ids

            # STEP 2: Run over categories with keywords in current topic
            for catitem in cat_items.filtered(lambda x: x.keywords):

                keywords = catitem.keywords.split(',')
                keywords = ['\\b' + kw.strip() + '\\b' for kw in keywords]

                # STEP 3: Run over current category keywords
                for keyword in keywords:
                    try:
                        regex = re.compile(keyword, re.IGNORECASE)
                        if self.findall(regex, _in_string):
                            result[record.id].append(catitem.id)

                    except Exception as ex:
                        _logger.warning(msg.format(
                            _in_string, catitem.keywords, str(ex)))

        return result
