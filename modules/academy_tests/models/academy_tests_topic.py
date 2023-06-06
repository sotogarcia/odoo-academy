# -*- coding: utf-8 -*-
""" AcademyTestsTopic

This module contains the academy.tests.topic Odoo model which stores
all academy tests topic attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN

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

    _inherit = [
        'ownership.mixin',
        'mail.thread'
    ]

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

    provisional = fields.Boolean(
        string='Provisional',
        required=False,
        readonly=False,
        index=True,
        default=False,
        help='Check it to indicate the topic is not definitive'
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    category_count = fields.Integer(
        string='Number of categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of categories',
        store=False,
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
        store=False,
        compute=lambda self: self.compute_question_count()
    )

    training_activity_ids = fields.Many2many(
        string='Activities',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all training activities that use this topic',
        comodel_name='academy.training.activity',
        relation='academy_training_activity_test_topic_rel',
        column1='test_topic_id',
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
        relation='academy_competency_unit_test_topic_rel',
        column1='test_topic_id',
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
        relation='academy_training_module_test_topic_rel',
        column1='test_topic_id',
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
            domain = [('topic_id', '=', record.id)]
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
            domain = [('topic_id', '=', record.id)]
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
            domain = [('topic_id', '=', record.id)]
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
            topic_ids = self._read_field_values(model, domain, 'topic_id.id')

            if topic_ids:
                result = [('id', 'in', topic_ids)]

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
