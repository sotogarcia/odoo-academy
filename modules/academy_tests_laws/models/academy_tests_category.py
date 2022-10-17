# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools.translate import _
from logging import getLogger
from odoo.exceptions import UserError
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN

from .utils.common import ART_REGEX, query_fetch_all_ids, \
    article_numbers, join_ints, split_value, clear_value

_logger = getLogger(__name__)


class AcademyTestsCategory(models.Model):
    """ Extends academy_tests.model_academy_tests_category adding new field
    to allow users to search records using spanish law patterns
    """

    _inherit = 'academy.tests.category'

    law = fields.Char(
        string='Range',
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

    def _compute_law(self):
        """ This is not implemented.
        # @api.depends('topic_id', 'category_ids')
        """
        for record in self:
            record.law = None

    def _search_by_law(self, operator, value):
        domain = FALSE_DOMAIN

        if value is False:
            domain = FALSE_DOMAIN if operator == '=' else TRUE_DOMAIN

        elif operator in ['=', '!=', 'ilike', 'not ilike']:

            value = clear_value(value)
            ignored, article_str = split_value(value)  # ignored is a law name
            articles = article_numbers(article_str)

            sql = self._get_search_by_law_base_sql()
            sql += self._and_clausule(operator, articles)

            category_ids = query_fetch_all_ids(self, sql)

            if category_ids:
                domain = [('id', 'in', category_ids)]

        else:
            msg = _('The operator {} is not supported for the Law field')
            raise UserError(msg.format(operator))

        return domain

    @staticmethod
    def _get_search_by_law_base_sql():
        return 'SELECT "id" FROM academy_tests_category WHERE TRUE'

    @staticmethod
    def _and_clausule(operator, articles):
        regex = ART_REGEX.format(art=join_ints(articles, '|'))
        if operator in ['=', '!=']:
            regex = '\\A{}\\Z'.format(regex)

        return ' AND "name" ~* \'{}\''.format(regex)
