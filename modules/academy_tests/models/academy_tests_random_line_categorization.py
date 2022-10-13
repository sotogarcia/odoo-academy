# -*- coding: utf-8 -*-
""" AcademyTestsRandomLineCategorization

This module contains the academy.tests.random.line.categorization an unique
Odoo model which contains required attributes and behavior to include/exclude
topics, versions and categories.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import AND, OR

from logging import getLogger

_logger = getLogger(__name__)

VERSION_IDS = 'topic_version_ids'
VERSION_ID = 'topic_version_id'


class AcademyTestsRandomLineCategorization(models.Model):
    """ Allow user to include or exclude topics, versions and categories
    in a random line
    """

    _name = 'academy.tests.random.line.categorization'
    _description = u'Academy tests random line categorization'

    _rec_name = 'id'
    _order = 'sequence ASC'

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this topic',
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
        help='Preference order for this answer'
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose topic to include/exclude',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_version_ids = fields.Many2many(
        string='Version list',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_topic_version_ids(),
        help='Choose the topic versions to include/exclude',
        comodel_name='academy.tests.topic.version',
        relation='academy_tests_random_line_categorization_topic_version_rel',
        column1='line_categorization_id',
        column2=VERSION_ID,
        domain=[],
        context={},
        limit=None
    )

    category_ids = fields.Many2many(
        string='Category list',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_category_ids(),
        help='Choose the topic categories to include/exclude',
        comodel_name='academy.tests.category',
        relation='academy_tests_random_line_categorization_category_rel',
        column1='line_categorization_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None
    )

    random_line_id = fields.Many2one(
        string='Random line',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose parent random line',
        comodel_name='academy.tests.random.line',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_version_count = fields.Integer(
        string='Topic versions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of chosen topic versions',
        store=False,
        compute=lambda self: self.compute_topic_version_count()
    )

    category_count = fields.Integer(
        string='Categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of chosen categories',
        store=False,
        compute=lambda self: self.compute_category_count()
    )

    @api.depends('topic_version_ids')
    def compute_topic_version_count(self):
        for record in self:
            record.topic_version_count = len(record.topic_version_ids)

    @api.depends('category_ids')
    def compute_category_count(self):
        for record in self:
            record.topic_category_count = len(record.category_ids)

    def _get_x2many(self, fname, sufix='items'):
        """ Get the single value from x2many field whose name matches the given
        whenever the field has only one value, otherwise, the number of records
        will be used instead.

        This method will be called from ``name_get``.

        Arguments:
            fname {str} -- name of target x2many field

        Keyword Arguments:
            sufix {str} -- text will follow the quantity (default: {'items'})

        Returns:
            str -- single value or number of records
        """

        result = _('No {}'.format(sufix))

        self.ensure_one()

        field = getattr(self, fname)
        if field:
            length = len(field)
            if length == 1:
                result = field.name
            else:
                result = _('{} {}'.format(length, sufix))

        return result

    def name_get(self):
        """ Computes the display name

        Display name will be formed by the name of the topic, the number of
        versions and the number of categories. If there is a single version
        or a single category, its name will be used insted quantity.

        Returns:
            {list} -- list of pairs (id, name) for all the items in recordset
        """

        pattern = '{} ({}) ({})'

        result = []

        for record in self:
            if record.topic_id:
                topic = record.topic_id.name
                versions = record._get_x2many(VERSION_IDS, 'versions')
                categories = record._get_x2many('category_ids', 'categories')

                name = pattern.format(topic, versions, categories)
            else:
                name = _('New')

            result.append((record.id, name))

        return result

    @api.onchange('topic_id')
    def _onchange_topic_id(self):
        for record in self:
            record.topic_version_ids = record.default_topic_version_ids()
            record.category_ids = record.default_category_ids()

        self.compute_topic_version_count()
        self.compute_category_count()

    def default_topic_version_ids(self):
        """ Computes default value for the topic version Many2many field, this
        will be the last version.

        Returns:
            mixed -- versions will be added or None
        """

        topic_version_ids = self.topic_id.topic_version_ids.sorted(
            lambda x: x.sequence, reverse=True)

        return topic_version_ids[0] if topic_version_ids else None

    def default_category_ids(self):
        """ Computes default value for the category Many2many field.

        If chosen topic has few categories all of them will be added, the
        field value will be empty if there are too many.

        Returns:
            mixed -- categories will be added or None
        """

        length = len(self.topic_id.category_ids)
        return self.topic_id.category_ids if length <= 3 else None

    def get_domain(self, exclude):
        """ Builds an unique normalized domain for all lines in recordset

        Arguments:
            exclude {bool} -- True to build a domain to found questions which
        questions that do not match with the domain

        Returns:
            [list] -- Odoo valid normalized domain
        """

        domains = []
        op_id = '!=' if exclude else '='
        op_ids = 'not in' if exclude else 'in'

        for record in self:

            line = []

            line.append([('topic_id', op_id, record.topic_id.id)])

            if record.topic_version_ids:
                ids = record.topic_version_ids.mapped('id')
                line.append([(VERSION_IDS, op_ids, ids)])

            if record.category_ids:
                ids = record.category_ids.mapped('id')
                line.append([('category_ids', op_ids, ids)])

            line = OR(line) if exclude else AND(line)

            domains.append(line)

        return AND(domains) if exclude else OR(domains)

