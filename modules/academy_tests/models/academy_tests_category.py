# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.category an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the real life category for question

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

"""


from logging import getLogger
import re


# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTestsCategory(models.Model):
    """ Category of the question

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.category'
    _description = u'Academy tests, question category'

    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'


    # ---------------------------- ENTITY FIEDS -------------------------------


    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this category',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this category',
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

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help=('Place of this category in the order of the categories from '
              'the topic')
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Topic to which this category belongs',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        # oldname='academy_topic_id',
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Questions relating to this category',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_category_rel',
        column1='category_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        # oldname='academy_question_ids'
    )

    keywords = fields.Char(
        string='Keywords',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Comma separated keywords',
        size=1024,
        translate=False
    )


    # --------------------------- SQL_CONTRAINTS ------------------------------


    _sql_constraints = [
        (
            'categoryr_by_topic_uniq',
            'UNIQUE(topic_id, name)',
            _(u'There is already another category with '
              'the same name in this topic')
        )
    ]


    # -------------------------- PYTHON_CONTRAINTS ----------------------------


    @api.constrains('keywords')
    def _check_keywords(self):
        """ Regular expresiones can be used as keywords. This constraint checks
        if given keywords can be compiled as regular expresions
        """

        message = _('Given keyword «{}» is not a valid regular expresion.\n'
                    'See https://docs.python.org/3/library/re.html')

        for record in self:
            keywords = (record.keywords or '').split(',')

            while keywords:
                keyword = keywords.pop()
                keyword = keyword.strip()

                if not self._is_valid_regular_expression(keyword):
                    raise ValidationError(message.format(keyword))


    @staticmethod
    def _is_valid_regular_expression(keyword):
        """ This method checks if given keyword can be compiled as python
        regular expresion. See https://docs.python.org/3/library/re.html

        @return (bool): true or false
        """

        result = True

        try:
            re.compile(keyword)
        except Exception:
            result = False

        return result
