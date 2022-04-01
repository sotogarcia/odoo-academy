# -*- coding: utf-8 -*-
""" AcademyTestsTopicVersion

This module contains the academy.tests.topic.version Odoo model which stores
all academy tests topic version attributes and behavior.
"""

from odoo import models, fields
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTopicVersion(models.Model):
    """ A topic can have more than one versions, this model represents these
    versions.
    """

    _name = 'academy.tests.topic.version'
    _description = u'Academy tests topic version'

    _rec_name = 'name'
    _order = 'sequence DESC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this version',
        size=1024,
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this version or uncheck to archivate'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this version',
        translate=True
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help=('Place of this version in the order of the versions from parent')
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the parent topic',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    provisional = fields.Boolean(
        string='Provisional',
        required=False,
        readonly=False,
        index=True,
        default=False,
        help='Check it to indicate the version is not definitive'
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
            domain = [('topic_version_id', '=', record.id)]
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
            domain = [('topic_version_id', '=', record.id)]
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
            domain = [('topic_version_id', '=', record.id)]
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
            topic_ids = self._read_field_values(
                model, domain, 'topic_version_id.id')

            if topic_ids:
                result = [('id', 'in', topic_ids)]

        return result

    _sql_constraints = [
        (
            'unique_version_by_topic',
            'UNIQUE("name", "topic_id")',
            _('There is already another version with the first name')
        )
    ]

