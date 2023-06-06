# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.test.question.rel an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the middle many to may relationship
between test and question, this additionally stores sequence order

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

"""

from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _

from io import BytesIO

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTestsTestQuestionRel(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.test.question.rel'
    _description = u'Academy tests, test-question relationship'

    _inherits = {
        'academy.tests.question': 'question_id'
    }

    _rec_name = 'test_id'
    _order = 'sequence ASC, id ASC'

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Test to which this item belongs',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question will be related with test',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    # This is a hack to use ID field to search in views
    real_question_id = fields.Integer(
        string='Question ID',
        related='question_id.id'
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Question sequence order'
    )

    # This only is used by 'view_academy_tests_test_question_rel_form' view
    perform = fields.Selection(
        string='Perform',
        required=False,
        readonly=False,
        index=False,
        default='link',
        help='Choose how the new link will be created',
        selection=[
            ('link', 'Link an existing question'),
            ('new', 'Create a new question')
        ]
    )

    index = fields.Integer(
        string='Index',
        required=False,
        readonly=True,
        index=False,
        default=1,
        help='Show the order of the question in the test',
        related="sequence",
        store=False
    )

    request_id = fields.Many2one(
        string='Request',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Show the request from which this link was created',
        comodel_name='academy.tests.question.request',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    test_block_id = fields.Many2one(
        string='Test block',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Choose the test block in which this question appears',
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='set null',
        auto_join=False
    )

    _sql_constraints = [
        (
            'prevent_duplicate_questions',
            'UNIQUE (test_id, question_id)',
            _(u'Duplicate question in test')
        )
    ]

    def name_get(self):
        result = []

        for record in self:
            if self.env.context.get('show_test_id', False):
                result.append((record.id, record.test_id.name))
            else:
                result.append((record.id, record.question_id.name))

        return result

    @api.model
    def fields_get(self, fields=None):

        fields = super(AcademyTestsTestQuestionRel, self).fields_get()

        selectable = self.question_id._selectable.copy()
        selectable.append('real_question_id')

        for field_name in fields.keys():
            fields[field_name]['selectable'] = field_name in selectable

        return fields

    def switch_status(self):
        """ This method is only a wrapper will be allows user to call
        the real switch_status existing in related question
        """

        question_ids = self.mapped('question_id')
        question_ids.switch_status()

    def _is_a_new_question(values):
        keys = values.keys()
        result = 'question_id 'not in keys
        result = result and 'name' in keys
        result = result and 'topic_id' in keys
        result = result and 'topic_version_ids' in keys
        result = result and 'category_ids' in keys
        result = result and 'type_id' in keys
        result = result and 'level_id' in keys
        result = result and 'owner_id' in keys
        result = result and 'answer_ids' in keys

        return result

    def _get_text_id(self, values):
        test_id = values.get('test_id')

        if not test_id:
            active_model = self.env.context.get('active_model', False)
            active_id = self.env.context.get('active_id', False)

            if active_model == 'academy.tests.test' and active_id:
                test_id = active_id

        return test_id

    @api.model
    def create(self, values):
        """ Ensure right sequence values. Allow to use given values valid to
        create question as link values dictionary. Ensure related a valid state
        in the related requests.
        """

        test_id = self._get_text_id(values)

        if test_id:
            link_obj = self.env['academy.tests.test.question.rel']
            link_set = link_obj.search([('test_id', '=', test_id)])
            sequences = link_set.mapped('sequence') or [0]
            values['sequence'] = max(sequences) + 1

        if 'question_id' not in values and 'name' in values:
            temp = values.copy()
            question_values = values.copy()

            question_values.pop('test_id')
            question_values.pop('sequence')

            question_item = self.env['academy.tests.question']
            question_item.create(question_values)

            values = {
                'test_id': temp.get('test_id', None),
                'question_id': question_item.id,
                'sequence': temp.get('sequence', 1)
            }

        _super = super(AcademyTestsTestQuestionRel, self)
        result = _super.create(values)

        request_set = result.mapped('request_id')
        request_set.update_state()

        return result

    def write(self, values):
        """ Ensure related a valid state in the related requests.
        """
        _super = super(AcademyTestsTestQuestionRel, self)
        result = _super.write(values)

        request_set = self.mapped('request_id')
        request_set.update_state()

        return result

    def unlink(self):
        """ Ensure related a valid state in the related requests.
        """

        request_set = self.mapped('request_id')

        _super = super(AcademyTestsTestQuestionRel, self)
        result = _super.unlink()

        request_set.update_state()

        return result

    def open_test(self):
        self.ensure_one()

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

    link_html = fields.Html(
        string='Link HTML',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show question as HTML',
        compute=lambda self: self.compute_link_html()
    )

    def compute_link_html(self):
        for record in self:
            record.link_html = record.to_html()

    def _get_values_for_template(self):
        self.ensure_one()

        result = self.question_id._get_values_for_template()
        result['index'] = self.sequence

        return result

    def to_html(self):
        output = ''

        template_xid = \
            'academy_tests.view_academy_tests_display_question_as_html'
        view_obj = self.env['ir.ui.view']

        for record in self:

            values = record._get_values_for_template()

            html = view_obj.render_template(template_xid, values)
            output += html.decode('utf8')

        return output

    def show_duplicates(self):
        return self.question_id.show_duplicates()

    def show_impugnments(self):
        return self.question_id.show_impugnments()

    def to_moodle(self, encoding='utf8', prettify=True, xml_declaration=True,
                  category=None, correction_scale=None):
        quiz = self.question_id._moodle_create_quiz(category=category)

        for record in self:
            name = 'SEQ-{:04}'.format(record.sequence)
            node = record.question_id._to_moodle(
                name=name, correction_scale=correction_scale)
            quiz.append(node)

        file = BytesIO()
        root = quiz.getroottree()
        root.write(file, encoding=encoding, pretty_print=prettify,
                   xml_declaration=xml_declaration)

        return file.getvalue()
