# -*- coding: utf-8 -*-
""" AcademyTestsCategory

This module contains the academy.tests.category Odoo model which stores
all academy tests category attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.osv.expression import FALSE_DOMAIN

from logging import getLogger
import re

_logger = getLogger(__name__)


class AcademyTestsCategory(models.Model):
    """ This is a property of the academy.tests.test model
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

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List the related questions',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_category_rel',
        column1='category_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    question_count = fields.Integer(
        string='Number of questions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of questions',
        store=False,
        compute=lambda self: self.compute_question_count()
    )

    provisional = fields.Boolean(
        string='Provisional',
        required=False,
        readonly=False,
        index=True,
        default=False,
        help='Check it to indicate the category is not definitive'
    )

    training_activity_ids = fields.Many2many(
        string='Activities',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all training activities that use this topic',
        comodel_name='academy.training.activity',
        relation='academy_training_activity_test_category_rel',
        column1='test_category_id',
        column2='training_activity_id',
        domain=[],
        context={},
        limit=None,
        store=False,
        compute='_compute_training_activity_ids',
        search='_search_training_activity_ids'
    )

    competency_unit_ids = fields.Many2many(
        string='Competency units',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all competency units that use this topic',
        comodel_name='academy.competency.unit',
        relation='academy_competency_unit_test_category_rel',
        column1='test_category_id',
        column2='competency_unit_id',
        domain=[],
        context={},
        limit=None,
        store=False,
        compute='_compute_competency_unit_ids',
        search='_search_competency_unit_ids'
    )

    training_module_ids = fields.Many2many(
        string='Modules',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all training modules that use this topic',
        comodel_name='academy.training.module',
        relation='academy_training_module_test_category_rel',
        column1='test_category_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None,
        store=False,
        compute='_compute_training_module_ids',
        search='_search_training_module_ids'
    )

    def _compute_training_activity_ids(self):
        for record in self:
            record.training_activity_ids = [(5, None, None)]

            model = 'academy.tests.topic.training.module.link'
            domain = [('category_ids.id', '=', record.id)]
            module_ids = self._read_field_values(
                model, domain, 'training_module_id.id')

            if module_ids:
                field_path = 'competency_unit_ids.training_module_id.id'
                domain = [(field_path, 'in', module_ids)]
                activity_set = self.env['academy.training.activity']
                activity_ids = activity_set.search(domain).mapped('id')

                if activity_ids:
                    record.training_activity_ids = [(6, None, activity_ids)]

    def _compute_competency_unit_ids(self):
        for record in self:
            record.competency_unit_ids = [(5, None, None)]

            model = 'academy.tests.topic.training.module.link'
            domain = [('category_ids.id', '=', record.id)]
            module_ids = self._read_field_values(
                model, domain, 'training_module_id.id')

            if module_ids:
                domain = [('training_module_id', 'in', module_ids)]
                competency_set = self.env['academy.competency.unit']
                competency_set = competency_set.search(domain)

                if competency_set:
                    competency_ids = competency_set.mapped('id')
                    record.competency_unit_ids = [(6, None, competency_ids)]

    def _compute_training_module_ids(self):
        for record in self:
            model = 'academy.tests.topic.training.module.link'
            domain = [('category_ids.id', '=', record.id)]
            module_ids = self._read_field_values(
                model, domain, 'training_module_id.id')

            if module_ids:
                record.training_module_ids = [(6, None, module_ids)]
            else:
                record.training_module_ids = [(5, None, None)]

    def _search_training_activity_ids(self, operator, value):

        domain = [('name', operator, value)]
        activity_set = self.env['academy.training.activity']
        activity_set = activity_set.search(domain)

        path = 'competency_unit_ids.training_module_id.id'
        module_ids = activity_set.mapped(path)

        domain = self._topic_domain_from_module_ids(module_ids)

        return domain

    def _search_competency_unit_ids(self, operator, value):

        domain = [('competency_name', operator, value)]
        competency_set = self.env['academy.competency.unit']
        competency_set = competency_set.search(domain)

        path = 'training_module_id.id'
        module_ids = competency_set.mapped(path)

        domain = self._topic_domain_from_module_ids(module_ids)

        return domain

    def _search_training_module_ids(self, operator, value):

        model = 'academy.training.module'
        domain = [('name', operator, value)]
        module_ids = self._read_field_values(model, domain, 'id')

        domain = self._topic_domain_from_module_ids(module_ids)

        return domain

    def _read_field_values(self, model, domain, field):
        model_obj = self.env[model]
        model_set = model_obj.search(domain)
        return model_set.mapped(field)

    def _topic_domain_from_module_ids(self, module_ids):
        result = FALSE_DOMAIN

        if module_ids:
            model = 'academy.tests.topic.training.module.link'
            domain = [('training_module_id', 'in', module_ids)]
            category_ids = self._read_field_values(
                model, domain, 'category_ids.id')

            if category_ids:
                result = [('id', 'in', category_ids)]

        return result

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
