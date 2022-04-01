# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.osv.expression import FALSE_DOMAIN
from logging import getLogger


_logger = getLogger(__name__)

WIZARD_STATES = [
    ('step1', 'Create version'),
    ('step2', 'Exclude questions')
]

NO_UPDATED_ACTION = [
    ('none', 'None'),
    ('draft', 'Set as draft'),
    ('new', 'Clone with new version'),
    ('new_draft', 'Clone as draft with new version'),
]

EXCLUDE_SQL = '''
    WITH has_given_categories AS (
        SELECT
            atq."id" AS question_id
        FROM
            academy_tests_question AS atq
        INNER JOIN academy_tests_question_category_rel AS crel
            ON crel.question_id = atq."id"
        INNER JOIN academy_tests_question_topic_version_rel AS vrel
            ON vrel.question_id = atq."id"
        WHERE
            topic_version_id = {ver}
            AND category_id IN ( {cats} )
    ) SELECT DISTINCT
        atq."id"
    FROM
        academy_tests_question AS atq
    INNER JOIN academy_tests_question_topic_version_rel AS vrel
        ON vrel.question_id = atq."id"
    LEFT JOIN has_given_categories AS hgc
        ON hgc.question_id = atq."id"
    WHERE
        topic_version_id = {ver}
        AND hgc.question_id {op} NULL
        --IS NOT
'''


class AcademyTestNewTopicVersion(models.TransientModel):
    """ Allow to create new version of the topic and apply it to the questions
    in selected categories
    """

    _name = 'academy.test.new.topic.version.wizard'
    _description = u'Academy test new topic version'

    _inherits = {'academy.tests.topic.version': 'topic_version_id'}

    _rec_name = 'id'
    _order = 'id ASC'

    chosen_category_ids = fields.Many2many(
        string='Categories',
        required=False,
        readonly=False,
        index=False,
        default=None,
        comodel_name='academy.tests.category',
        relation='academy_test_new_topic_version_wizard_category_rel',
        column1='wizard_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None,
        help=('Categories contain the questions to which the new version will '
              'not be added')
    )

    topic_version_id = fields.Many2one(
        string='Topic version',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='New topic version will be created',
        comodel_name='academy.tests.topic.version',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    update_questions = fields.Boolean(
        string='Append version',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check this to append new version to the existing questions'
    )

    no_updated = fields.Selection(
        string='With excluded',
        required=True,
        readonly=False,
        index=False,
        default='none',
        selection=NO_UPDATED_ACTION,
        help=('Choose what will be done with questions that have not been '
              'updated')
    )

    state = fields.Selection(
        string='State',
        required=False,
        readonly=False,
        index=False,
        default='step1',
        help='Current wizard step',
        selection=WIZARD_STATES
    )

    @api.model
    def default_get(self, default_fields):
        """ Override main method to append some values obtained from context

        This checks if active model is a topic and then pick up the active id
        and set it as default value for topic_id field.

        Decorators:
            api.model

        Arguments:
            default_fields {list} -- list of fields will be updated

        Returns:
            dict -- dictionary with pairs field-value
        """

        _super = super(AcademyTestNewTopicVersion, self)
        values = _super.default_get(default_fields)

        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model == 'academy.tests.topic' and active_id:
            values['topic_id'] = active_id

            topic_item = self.env[active_model].browse(active_id)
            versions = topic_item.topic_version_ids.mapped('sequence')
            values['sequence'] = max(versions or [0]) + 10

        return values

    @api.onchange('topic_id')
    def _onchange_topic_id(self):
        """ When changing the subject, the chosen categories must be those
        belonging to the topic

        Decorators:
            api.onchange
        """

        for record in self:
            record.chosen_category_ids = [(5, 0, 0)]

    @api.onchange('update_questions')
    def _onchange_update_questions(self):
        """ If questions are not updated they are not set as draft either

        Decorators:
            api.onchange
        """
        for record in self:
            if not record.update_questions:
                self.no_updated = 'none'

    def _get_previous_version_id(self, new_id):
        """ Use sequence field to get the last version in topic before this
        new one

        Arguments:
            new_id {int} -- ID of the current created version

        Returns:
            mixed -- ID of the previous version or None
        """

        version_obj = self.env['academy.tests.topic.version']

        domain = [('topic_id', '=', self.topic_id.id), ('id', '!=', new_id)]
        rows = version_obj.search_read(
            domain, ['id', 'name'], limit=1, order='sequence DESC')

        print(rows)

        return rows[0]['id'] if rows else None

    @staticmethod
    def _except(whole, to_exclude):
        return [item for item in whole if item not in to_exclude]

    def _read_topic_version_id(self):
        return self.topic_version_id.id

    def _read_topic_category_ids(self):
        return self.topic_id.mapped('category_ids.id')

    def _read_chosen_category_ids(self):
        return self.chosen_category_ids.mapped('id')

    def _update_questions(self, domain, values):
        question_obj = self.env['academy.tests.question']
        question_set = question_obj.search(domain)

        question_set.write(values)

    def _clone_questions(self, domain, defaults):
        """ Perform a copy of the questions that match the domain, overwriting
        some of the attributes.

        Arguments:
            domain {list} -- Odoo valid domain for questions
            defaults {dict} -- Dictionary {field: value} to overwrite

        Returns:
            recordset -- recorset of the copies of questions
        """

        result_set = self.env['academy.tests.question']
        question_set = self.env['academy.tests.question']
        question_set = result_set.search(domain)

        for question_item in question_set:
            result_set += question_item.copy(defaults)
        print(domain)

        return result_set

    def _build_domain(self, version_id, category_ids, exclude=False):
        op = 'IS NOT' if exclude else 'IS'
        joined = ', '.join([str(item) for item in category_ids])
        sql = EXCLUDE_SQL.format(ver=version_id, cats=joined, op=op)

        self.env.cr.execute(sql)
        rows = self.env.cr.dictfetchall()

        if not rows:
            return FALSE_DOMAIN

        question_ids = [row['id'] for row in (rows or [])]

        return [('id', 'in', question_ids)]

    def _append_version(self, version_id, last_version_id):
        """ Append new created version to those questions have at least one of
        the chosen categories.

        Returns:
            list -- list of the category ids have been updated
        """

        category_ids = self._read_chosen_category_ids()

        if category_ids and last_version_id:
            domain = self._build_domain(
                last_version_id, category_ids, False)
            values = {'topic_version_ids': [(4, version_id, None)]}

            self._update_questions(domain, values)

        return category_ids

    def _with_no_updated(self, version_id, last_version_id, updated_ids):
        """ Perform subsequent action with no updated questions.

        Arguments:
            updated_ids {list} -- ID of the questions were previously updated
        """

        category_ids = self._read_chosen_category_ids()

        if category_ids:

            target_domain = self._build_domain(
                last_version_id, category_ids, True)

            if self.no_updated == 'draft':
                values = dict(status='draft')
                self._update_questions(target_domain, values)

            elif self.no_updated in ['new', 'new_draft']:
                version_id = self._read_topic_version_id()
                values = {'topic_version_ids': [(6, None, [version_id])]}

                if self.no_updated == 'new_draft':
                    values['status'] = 'draft'

                self._clone_questions(target_domain, values)

    def append_version(self):
        """ Append created topic version to all the questions which have at
        least one of the chosen categories.

        This method will be invoked by a button in Wizard
        """
        for record in self:

            if record.update_questions:
                version_id = self._read_topic_version_id()
                last_version_id = self._get_previous_version_id(version_id)

                category_ids = record._append_version(
                    version_id, last_version_id)

                if record.no_updated != 'none':
                    record._with_no_updated(
                        version_id, last_version_id, updated_ids=category_ids)
