# -*- coding: utf-8 -*-
""" AcademyTestsTopic

This module contains the academy.tests.topic Odoo model which stores
all academy tests topic attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _

import re
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTopic(models.Model):
    """ This is a property of the academy.tests.question model
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
        size=1024,
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
    )

    question_ids = fields.One2many(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List the related questions',
        comodel_name='academy.tests.question',
        inverse_name='topic_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    topic_version_ids = fields.One2many(
        string='Versions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Manage different versions of the same topic',
        comodel_name='academy.tests.topic.version',
        inverse_name='topic_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
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

    @api.onchange('category_ids')
    def _onchange_category_ids(self):
        self.compute_category_count()

    question_count = fields.Integer(
        string='Number of questions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of questions',
        compute=lambda self: self.compute_question_count()
    )

    @api.depends('question_ids')
    def compute_question_count(self):
        """ Computes `question_count` field value, this will be the number
        of categories related with this topic
        """
        for record in self:
            record.question_count = len(record.question_ids)

    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'category_uniq',
            'UNIQUE(name)',
            _(u'There is already another topic with the same name')
        )
    ]

    # --------------------------- PUBLIC METHODS ------------------------------

    def last_version(self, topic_id=None):
        item = topic_id or self

        versions = item.topic_version_ids.sorted(key='sequence', reverse=True)

        return versions[0] if versions else False

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

    def append_version(self):
        self.ensure_one()

        action = {
            'type': 'ir.actions.act_window',
            'name': 'New topic version wizard',
            'res_model': 'academy.test.new.topic.version.wizard',
            'view_mode': 'form',
            'target': 'new',
            'domain': [],
            'context': {'active_model': self._name, 'active_id': self.id},
        }

        return action
