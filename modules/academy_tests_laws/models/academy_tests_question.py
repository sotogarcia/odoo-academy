# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from .utils.sql_inverse_searches import SEARCH_BY_LAW_SQL

from .utils.common import LAW_REGEX, ART_REGEX, query_fetch_all_ids, \
    article_numbers, join_ints, split_value, clear_value

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsQuestion(models.Model):
    """ Extends academy_tests.model_academy_tests_question adding new field
    to allow users to search records using spanish law patterns
    """

    _inherit = ['academy.tests.question']

    law = fields.Char(
        string='Law',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Allow users to search records using spanish law patterns',
        size=255,
        translate=False,
        store=False,
        compute='_compute_law',
        search='_search_by_law'
    )

    def init(self):
        """ This method is called after :meth:`~._auto_init`, and may be
            overridden to create or modify a model's database schema.
        """
        pass

    def _compute_law(self):
        """ This is not implemented.
        # @api.depends('topic_id', 'category_ids')
        """
        for record in self:
            record.law = None

    def _search_by_law(self, operator, value):
        domain = [('id', '=', -1)]

        if operator in ['=', '!='] and value is False:

            sql = self._get_search_by_law_base_sql()
            question_ids = self._get_question_ids(sql)

            in_operator = 'in' if operator == '!=' else 'not in'
            domain = [('id', in_operator, question_ids)]

        elif operator in ['=', '!=', 'ilike', 'not ilike']:

            value = clear_value(value)
            law, article_str = split_value(value)
            articles = article_numbers(article_str)

            if law or articles:
                sql = self._get_search_by_law_base_sql(
                    bool(law), bool(articles))

                if law:
                    law_leaf = self._law_leaf(operator, law)
                    sql += ' AND {}'.format(law_leaf)

                if articles:
                    articles_leaf = self._articles_leaf(articles)
                    sql += ' AND {}'.format(articles_leaf)

                question_ids = query_fetch_all_ids(self, sql)

                domain = [('id', 'in', question_ids)]

        else:
            msg = _('The operator {} is not supported for the Law field')
            raise UserError(msg.format(operator))

        return domain

    @staticmethod
    def _get_search_by_law_base_sql(law=True, article=True):
        with_and = ''
        all_articles = ART_REGEX.format(art='[0-9]+')

        if law:
            with_and += ' AND att."name" ~* \'{}\''.format(LAW_REGEX)

        if article:
            with_and += ' AND atc."name" ~* \'{}\''.format(all_articles)

        return SEARCH_BY_LAW_SQL.format(
            law=LAW_REGEX, art=all_articles, wand=with_and)

    @staticmethod
    def _law_leaf(operator, value):
        if operator == 'ilike' or operator == 'not ilike':
            result = '"law" {} \'%{}%\''.format(operator, value)
        else:
            result = '"law" {} \'{}\''.format(operator, value)

        return result

    @classmethod
    def _articles_leaf(cls, articles):
        return '"article" IN ({})'.format(join_ints(articles))

    @api.model
    def fields_get(self, fields=None):

        fields = super(AcademyTestsQuestion, self).fields_get()

        fields['law']['selectable'] = True

        return fields
