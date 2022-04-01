# -*- coding: utf-8 -*-
""" Academy Tests Question Import

This module contains the academy.tests.question.import model
which contains all Import wizzard attributes and behavior.

This model is the a wizard  to import questions from text
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError


from collections import Counter
from datetime import datetime

from logging import getLogger

_logger = getLogger(__name__)


QUESTION_TEMPLATE = _('''
> Optional comment for question
Optional preamble to the question
![Image title](image name or ID)
1. Question text
a) Answer 1
b) Answer 2
c) Answer 3
x) Right answer
''')

WIZARD_STATES = [
    ('step1', 'Prerequisites'),
    ('step2', 'Content')
]


# pylint: disable=locally-disabled, R0903, W0212, E1101
class AcademyTestsQuestionImport(models.TransientModel):
    """ This model is the a wizard  to import questions from text
    """

    _name = 'academy.tests.question.import.wizard'
    _description = u'Academy tests, question import'

    _rec_name = 'id'
    _order = 'id DESC'

    _inherit = ['academy.abstract.owner', 'academy.abstract.import.export']

    test_id = fields.Many2one(
        string='Test',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_test_id(),
        help='Choose test to which questions will be append',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Questions has been created',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_import_question_rel',
        column1='question_import_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
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

    content = fields.Text(
        string='Content',
        required=True,
        readonly=False,
        index=False,
        default=QUESTION_TEMPLATE,
        help='Text will be processed to create new questions',
        translate=True
    )

    attachment_ids = fields.Many2many(
        string='Attachments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Attachment has been created',
        comodel_name='ir.attachment',
        relation='academy_tests_question_import_ir_attachment_rel',
        column1='question_import_id',
        column2='attachment_id',
        domain=[
            '|',
            ('res_model', '=', False),
            ('res_model', '=', 'academy.tests.question.import.wizard')
        ],
        context={
            'import_wizard': True,
            'tree_view_ref': 'academy_tests.view_ir_attachment_tree',
            'form_view_ref': 'academy_tests.view_ir_attachment_form',
            'search_view_ref': 'academy_tests.view_attachment_search',
            'search_default_my_documents_filter': 0,
            'search_default_my_own_documents_filter': 1
        },
        limit=None
    )

    imported_attachment_ids = fields.Many2many(
        string='Imported attachments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Attachment has been created',
        comodel_name='ir.attachment',
        relation='academy_tests_question_import_imported_ir_attachment_rel',
        column1='question_import_id',
        column2='attachment_id',
        domain=[],
        context={'import_wizard': True},
        limit=None
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_topic_id(),
        help='Choose topic will be used for new questions',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    topic_version_ids = fields.Many2many(
        string='Topic versions',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose which versions of the topic this question belongs to',
        comodel_name='academy.tests.topic.version',
        relation='academy_tests_question_import_topic_version_rel',
        column1='question_import_id',
        column2='topic_version_id',
        domain=[],
        context={},
        limit=None
    )

    category_ids = fields.Many2many(
        string='Categories',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose categories will be used for new questions',
        comodel_name='academy.tests.category',
        relation='academy_tests_question_import_category_rel',
        column1='question_import_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None
    )

    type_id = fields.Many2one(
        string='Type',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_type_id(),
        help='Choose type will be used for imported questions',
        comodel_name='academy.tests.question.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    level_id = fields.Many2one(
        string='Difficulty',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_level_id(),
        help='Choose level will be used for imported questions',
        comodel_name='academy.tests.level',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    tag_ids = fields.Many2many(
        string='Tags',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Choose tags will be used for imported questions',
        comodel_name='academy.tests.tag',
        relation='academy_tests_question_import_tag_rel',
        column1='question_import_id',
        column2='tag_id',
        domain=[],
        context={},
        limit=None
    )

    autocategorize = fields.Boolean(
        string='Autocategorize',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Check to autoset categories using keywords'
    )

    status = fields.Selection(
        string='Status',
        required=False,
        readonly=False,
        index=False,
        default='ready',
        help='Switch question status',
        selection=[
            ('draft', 'Draft'),
            ('ready', 'Ready')
        ]
    )

    authorship = fields.Boolean(
        string='Authorship',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to indicate that it is your own authorship'
    )

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_name(),
        help="Name for this test",
        size=255,
        translate=True,
    )

    check_categorization = fields.Boolean(
        string='Check categorization',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to perform a manual categorization check'
    )

    sequential = fields.Boolean(
        string='Sequential',
        required=False,
        readonly=False,
        index=True,
        default=False,
        help='Check it to indicate that the questions are chained'
    )

    # ----------------- EVENTS AND AUXILIARY FIELD METHODS --------------------

    def default_test_id(self):
        result_set = self.env['academy.tests.test']

        context = self.env.context or {}
        active_model = context.get('active_model', False)
        active_id = context.get('active_id', False)

        if active_model == 'academy.tests.test' and active_id:
            result_set = self.env[active_model].browse(active_id)

        return result_set

    def default_topic_id(self):
        """ This returns most frecuency used topic id
        """

        xid = 'academy_tests.academy_tests_topic_no_topic'
        topic_item = self.env.ref(xid)

        if not self.env.context.get('create_new_test', False):
            exclude = [('id', '<>', topic_item.id)]
            topic_item = self._most_frecuent('topic_id', domain=exclude)

        return topic_item

    def default_type_id(self):
        """ This returns most frecuency used type id
        """
        return self._most_frecuent('type_id')

    def default_level_id(self):
        """ This returns most frecuency used level id
        """
        return self._most_frecuent('level_id')

    def default_name(self):
        test = _('Test')
        time = datetime.now().strftime('%Y·%M·%d-%H·%M·%S')

        return '{}-{}'.format(test, time)

    @api.onchange('topic_id')
    def _onchange_topid_id(self):
        """ Removes version and categories
        """
        xid = 'academy_tests.academy_tests_topic_no_topic'
        topic_item = self.env.ref(xid)

        if self.topic_id.id == topic_item.id:
            xid = 'academy_tests.academy_tests_topic_version_no_version'
            item = self.env.ref(xid)
            self.topic_version_ids = [(6, 0, [item.id])]

            xid = 'academy_tests.academy_tests_category_no_category'
            item = self.env.ref(xid)
            self.category_ids = [(6, 0, [item.id])]
        else:
            self.topic_version_ids = self.topic_id.last_version()
            self.category_ids = [(5, 0, 0)]

    @api.onchange('state')
    def _onchange_state(self):

        # pylint: disable=locally-disabled, E1101
        if self.imported_attachment_ids:
            self._move_imported_attachments()

        if self.state != 'step1' and not (self.topic_id and self.category_ids):
            self.state = 'step1'
            return {
                'warning': {
                    'title': _('Required'),
                    'message': _('Topic and categories are '
                                 'required before continue')
                }
            }

        return False

    # --------------------------- PUBLIC METHODS ------------------------------

    def process_text(self):
        """ Perform job """

        if not (self.topic_id and self.category_ids):
            message = _('Topic and categories are not optional')
            raise ValidationError(message)

        if self.env.context.get('create_new_test', False):
            values = {'name': self.name}
            test_obj = self.env['academy.tests.test']
            self.test_id = test_obj.create(values)

        content = self.clear_text(self.content)
        groups = self.split_in_line_groups(content)
        value_set = self.build_value_set(groups, update=False)

        self.postprocess_attachment_ids(value_set, self.attachment_ids)

        self._append_categorization(value_set)

        if self.autocategorize:
            self.auto_set_categories(value_set, self.topic_id)

        if self.owner_field_is_accessible(self):
            self.assign_to(self.attachment_ids, self.owner_id)
            self.append_owner(value_set, self.owner_id)

        self.question_ids = self.create_questions(value_set, self.sequential)

        if self.test_id:
            question_set = self.question_ids.sorted(
                key=lambda q: q.id, reverse=False)
            self.append_to_test(self.test_id, question_set)

        return self._close_wizard_and_redirect()

    def _close_wizard_and_redirect(self):
        self.ensure_one()

        if self.check_categorization:
            result = self._manual_categorization_act_window()

        elif self.test_id and not self._is_in_the_target_test():
            result = self._test_form_act_window()

        else:
            result = self._questions_act_window()

        return result

    def _manual_categorization_act_window(self):
        act_xid = ('academy_tests.'
                   'action_academy_tests_manual_categorization_act_window')
        result = self.env.ref(act_xid).read()[0]

        question_ids = self.question_ids.mapped('id')

        result['target'] = 'main'
        result['name'] = _('Imported questions')
        result['domain'] = [('id', 'in', question_ids)]

        return result

    def _test_form_act_window(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.tests.test',
            'view_mode': 'form',
            'res_id': self.test_id.id,
            'target': 'main',
            'flags': {
                'form': {
                    'action_buttons': True, 'options': {'mode': 'edit'}
                }
            }
        }

    def _questions_act_window(self):
        act_xid = 'academy_tests.action_questions_act_window'
        result = self.env.ref(act_xid).read()[0]

        result['target'] = 'main'
        result['context'] = {}  # Remove filters

        return result

    def _is_in_the_target_test(self):

        result = False

        params = self.env.context.get('params', False) or {}

        if params:
            model = params.get('model', False)
            active_id = params.get('id', False)

            result = (model == 'academy.tests.test') and \
                     (active_id == self.test_id.id)

        return result

    # -------------------------------------------------------------------------

    def _append_categorization(self, values_set):
        # pylint: disable=locally-disabled, E1101
        catops = [(4, ID, None) for ID in self.category_ids.mapped('id')]
        tagops = [(4, ID, None) for ID in self.tag_ids.mapped('id')]
        verops = [(4, ID, None) for ID in self.topic_version_ids.mapped('id')]

        categorization_values = {
            'topic_id': self.topic_id.id,
            'topic_version_ids': verops,
            'category_ids': catops,
            'type_id': self.type_id.id,
            'tag_ids': tagops,
            'level_id': self.level_id.id,
            'authorship': self.authorship
        }

        for values in values_set:
            values.update(categorization_values)

    def _move_imported_attachments(self):
        """ Appends imported files to list of available attachments and
        removes from list of imported
        """

        _ids = self.imported_attachment_ids.mapped('id')
        self.attachment_ids = [(4, _id, None) for _id in _ids]
        self.imported_attachment_ids = [(5, None, None)]

    def _most_frecuent(self, fname, domain=None):

        uid = self.env.context['uid']
        mode = False
        domain = domain or []

        domain.append(('owner_id', '=', uid))
        order = 'create_date DESC'
        question_obj = self.env['academy.tests.question']
        question_set = question_obj.search(domain, limit=100, order=order)

        if question_set:
            ids = []
            for question_item in question_set:
                target = getattr(question_item, fname)
                ids.extend(target.mapped('id'))

            result = Counter(ids).most_common(1)
            if result:
                mode = result[0][0]

        return mode
