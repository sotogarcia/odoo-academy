# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _
from logging import getLogger

import hashlib
import json

_logger = getLogger(__name__)


class AcademyTestsUpdateQuestionsWizard(models.TransientModel):
    """ Wizard which can be used to update existing questions using markdown
    """

    _name = 'academy.tests.update.questions.wizard'
    _description = u'Academy tests update questions wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    _inherit = ['academy.abstract.import.export']

    state = fields.Selection(
        string='State',
        required=False,
        readonly=False,
        index=False,
        default='step1',
        help='Current wizard step',
        selection=[
            ('step1', 'Text'),
            ('step2', 'Attachments')
        ]
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_question_ids(),
        help='Choose the existing questions will be updated',
        comodel_name='academy.tests.question',
        relation='academy_tests_update_wizard_question_rel',
        column1='wizard_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    markdown = fields.Text(
        string='Markdown',
        required=True,
        readonly=False,
        index=False,
        default='',
        help='Markdown text will be used to update the chosen questions',
        translate=False,
    )

    ir_attachment_ids = fields.Many2many(
        string='Attachments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='All the available attachments can be used in chosen questions',
        comodel_name='ir.attachment',
        relation='academy_tests_update_wizard_ir_attachment_rel',
        column1='wizard_id',
        column2='attachment_id',
        domain=[
            ('res_model', '=', False)
        ],
        context={},
        limit=None,
    )

    zip_file = fields.Binary(
        string='Zip file',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Upload a zip file with attachment updates',
        store=False
    )

    text_file = fields.Binary(
        string='Text file',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Upload a text file with question updates',
        store=False
    )

    text_encoding = fields.Selection(
        string='Encoding',
        required=True,
        readonly=False,
        index=False,
        default='auto',
        help=False,
        selection=[
            ('auto', 'Autodetect'),
            ('cp1252', 'Windows 1252'),
            ('utf_16_be', 'UTF-16BE'),
            ('utf_16_le', 'UTF-16LE'),
            ('utf_8', 'UTF-8'),
            ('utf_8_sig', 'UTF-8 with BOM'),
            ('cp850', 'IBM 850')
        ]
    )

    @api.onchange('text_file')
    def _onchange_text_file(self):
        if self.text_file:

            content = self._field_to_string(self.text_file)
            content = self.decode_content(content, self.text_encoding)

            self.markdown = self.clear_text(content)

    @api.onchange('text_encoding')
    def _onchange_text_encoding(self):
        if self.text_file:

            content = self._field_to_string(self.text_file)
            content = self.decode_content(content, self.text_encoding)

            self.markdown = self.clear_text(content)

    @api.onchange('zip_file')
    def _onchange_zip_file(self):
        if self.zip_file:
            try:
                available_ids = self._get_real_ids(self.ir_attachment_ids)

                io = self._field_to_bytesio(self.zip_file)
                self.ensure_zip_format(io)

                self.validate_filenames(io, available_ids)

                content = self.read_statement_from_zip(io)
                if content:
                    self.markdown = self.clear_text(content)

            except ValidationError as ve:
                self.zip_file = False
                return {
                    'warning': {
                        'title': _('Validation error'),
                        'message': ve.name
                    }
                }

    def default_question_ids(self):
        question_obj = self.env['academy.tests.question']

        context = self.env.context
        active_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if active_model == 'academy.tests.test.question.rel':
            active_ids = self._get_mapped(
                active_model, active_ids, 'question_id.id')
        elif active_model == 'academy.tests.test':
            active_ids = self._get_mapped(
                active_model, active_ids, 'question_ids.question_id.id')

        return question_obj.search([('id', 'in', active_ids)])

    @api.onchange('question_ids')
    def _onchange_question_ids(self):
        self.ensure_one

        question_set = self._search_for_real_questions()

        attach_ids = question_set.mapped('ir_attachment_ids.id')
        m2m_action = [(6, 0, attach_ids) if attach_ids else (5, 0, 0)]

        content = question_set.to_string(True)
        self.markdown = self.clear_text(content)
        self.ir_attachment_ids = m2m_action

    def _search_for_real_questions(self):
        error_msg = 'Expected questions { }, found questions {}'

        question_set = self.mapped('question_ids')
        question_ids = [item._origin.id for item in question_set]
        question_set = question_set.search([('id', 'in', question_ids)])

        assert len(question_ids) == len(question_set), \
            _(error_msg.format(len(question_ids), len(question_set)))

        return question_set

    def _get_mapped(self, model_name, ids, path):
        """ This method is used in ``default_question_ids``
        """

        item_obj = self.env[model_name]
        item_set = item_obj.search([('id', 'in', ids)])

        return item_set.mapped(path)

    @staticmethod
    def _remove_dependent_fields(values):
        if 'question_ids' in values:
            for field_name in ['markdown', 'ir_attachment_ids']:
                if field_name in values:
                    values.pop(field_name)

    @api.model
    def create(self, values):
        """ Create a new record for a model AcademyTestsUpdateQuestionsWizard
            @param values: provides a data for new record

            @return: returns a id of new record
        """

        _super = super(AcademyTestsUpdateQuestionsWizard, self)
        result = _super.create(values)

        return result

    def write(self, values):
        """ Update records

            @param values: dict of new values to be set

            @return: True on success, False otherwise
        """

        _super = super(AcademyTestsUpdateQuestionsWizard, self)
        result = _super.write(values)

        return result

    def process_text(self):
        """ Perform job """

        content = self.clear_text(self.markdown)
        groups = self.split_in_line_groups(content)
        value_set = self.build_value_set(groups, update=True)
        self.postprocess_attachment_ids(value_set, self.ir_attachment_ids)

        self.write_questions(value_set, self.question_ids)

    def save_as_zip(self):
        question_ids = self._ensure_ids(self.question_ids)
        param = ','.join([str(item) for item in question_ids])

        return {
            'type': 'ir.actions.act_url',
            'url': '/academy_tests/source?question_ids={}'.format(param),
            'target': 'blank'
        }

    def set_questions(self, question_set):
        for record in self:
            record.question_ids = question_set
            record._onchange_question_ids()
