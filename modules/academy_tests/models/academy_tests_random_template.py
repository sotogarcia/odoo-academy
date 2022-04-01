# -*- coding: utf-8 -*-
""" AcademyTestsRandomTemplate

This module contains the academy.tests.random.templeate Odoo model which stores
all academy tests random templeate attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.osv.expression import AND
from odoo.osv.expression import TRUE_DOMAIN
from .utils.libuseful import eval_domain
from enum import IntFlag

from datetime import datetime

from logging import getLogger

_logger = getLogger(__name__)


class OverwriteInfo(IntFlag):
    NONE = 0
    QUESTIONS = 3
    TESTINFO = 5
    ALL = 7


class AcademyTestsRandomTemplate(models.Model):
    """ Random templates stores a set of lines can be used to automatically
    fill an existing test with questions
    """

    _name = 'academy.tests.random.template'
    _description = u'Academy Tests Random Template'

    _inherit = ['academy.abstract.owner', 'image.mixin', 'mail.thread']

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
        translate=True,
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    random_line_ids = fields.One2many(
        string='Criteria',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.random.line',
        inverse_name='random_template_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        copy=True
    )

    test_ids = fields.One2many(
        string='Used in',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        inverse_name='random_template_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        copy=False
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Maximum number of questions can be appended',
        compute='compute_quantity',
        wizard=True
    )

    lines_count = fields.Integer(
        string='Nº lines',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of lines',
        store=False,
        compute='compute_line_count'
    )

    scheduled_ids = fields.One2many(
        string='Scheduled tasks',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Schedule this template',
        comodel_name='academy.tests.random.template.scheduled',
        inverse_name='template_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        copy=False
    )

    scheduled_count = fields.Integer(
        string='Nº of scheduled',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of scheduled tasks',
        compute=lambda self: self.compute_scheduled_count()
    )

    incremental = fields.Selection(
        string='Incremental',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Exclude questions previously selected by this template',
        selection=[
            ('tpl', 'Template'),
            ('usr', 'Active user'),
            ('tplusr', 'Template/Active user')
        ],
        wizard=True
    )

    @api.depends('scheduled_ids')
    def compute_scheduled_count(self):
        for record in self:
            record.scheduled_count = len(record.scheduled_ids)

    @api.onchange('scheduled_ids')
    def _onchange_scheduled_ids(self):
        self.compute_scheduled_count()

    # ------------------------ TEST INFORMATION ------------------------

    time_by = fields.Selection(
        string='Time by',
        required=False,
        readonly=False,
        index=False,
        default='test',
        help=False,
        selection=[('test', 'Test'), ('question', 'Question')],
        wizard=True
    )

    available_time = fields.Float(
        string='Time',
        required=False,
        readonly=False,
        index=False,
        default=0.5,
        digits=(16, 2),
        help='Available time to complete the exercise',
        wizard=True
    )

    lock_time = fields.Boolean(
        string='Lock time',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Check to not allow the user to continue with the test once the '
              'time has passed'),
        wizard=True
    )

    correction_scale_id = fields.Many2one(
        string='Correction scale',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_correction_scale_id(),
        help='Choose the scale of correction',
        comodel_name='academy.tests.correction.scale',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        wizard=True
    )

    test_kind_id = fields.Many2one(
        string='Kind of test',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the kind for this test',
        comodel_name='academy.tests.test.kind',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        wizard=True
    )

    preamble = fields.Text(
        string='Preamble',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='What it is said before beginning to test',
        translate=True,
        wizard=True
    )

    test_description = fields.Text(
        string='Test description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about the test',
        translate=True,
        wizard=True
    )

    skip_faulty_lines = fields.Boolean(
        string='Skip faulty',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to skip faulty lines',
        wizard=True
    )

    name_pattern = fields.Char(
        string='Name pattern',
        required=False,
        readonly=False,
        index=False,
        default='{template} %m/%d/%Y - {sequence}',
        help='Pattern will be used to create names to the new tests',
        size=50,
        translate=True,
        wizard=True
    )

    context_ref = fields.Reference(
        string='Context',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Choose context in which this template will be used',
        selection=[
            ('academy.training.action', 'Training action'),
            ('academy.training.action.enrolment', 'Student enrolment'),
        ],
        wizard=True
    )

    parent_id = fields.Many2one(
        string='Parent',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose parent template',
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    # ----------------- AUXILIARY FIELDS METHODS AND EVENTS -------------------

    def default_correction_scale_id(self):
        xid = 'academy_tests.academy_tests_correction_scale_default'
        result = self.env.ref(xid)

        return result.id if result else None

    @api.depends('random_line_ids')
    def compute_quantity(self):
        """ This computes lines_count field """
        for record in self:
            values = record.random_line_ids.mapped('quantity')
            record.quantity = sum(values)

    @api.depends('random_line_ids')
    def compute_line_count(self):
        """ This computes lines_count field """
        for record in self:
            record.lines_count = len(record.random_line_ids)

    @api.model
    def _domain_for_ir_cron_id(self):
        module = 'academy_tests'
        name = 'model_academy_tests_random_template'

        md_domain = [('module', '=', module), ('name', '=', name)]
        md_obj = self.env['ir.model.data']
        md_set = md_obj.search(md_domain)

        return [('model_id', '=', md_set.res_id)]

    # -------------------------- AUXILIARY METHODS ----------------------------

    def _compute_base_sequence_value(self, test_id):
        """ Get the greater sequence value of the set of questions in test
        and returns it. If there are no questions the returned value will be 0

        @note: this is not a ordinary compute method
        @note: next sequence must be ``returned value + 1``
        """

        sequences = test_id.question_ids.mapped('sequence') or [0]
        return (max(sequences)) + 0

    def _get_base_values(self, test_id, sequence):
        """ Builds a dictionary with the required values to create a new
        ``academy.tests.test.question.rel`` record, this will act as a link
        between given test and future question
        """

        return {
            'test_id': test_id.id,
            'question_id': None,
            'sequence': sequence
        }

    @classmethod
    def _build_many2many_write_action(cls, question_set, base_values):
        leafs = []
        values = cls._dict_copy(base_values)

        for question in question_set:
            values['question_id'] = question.id
            values['sequence'] = values['sequence'] + 1

            leafs.append((0, None, cls._dict_copy(values)))

        return leafs

    def _perform_many2many_write_action(self, leafs, test_id):
        return test_id.write({'question_ids': leafs})

    @staticmethod
    def _dict_copy(in_dict):
        return in_dict.copy() if in_dict else {}

    # ---------------------------- PUBIC METHODS ------------------------------

    def assert_expected_questions(self, items):
        """ Check if are there enough questions in given recordset to supply
        required by the template

        Arguments:
            items {recordset|list} -- question recordset or x2many
            operations will be checked

        Raises:
            UserError -- if the length of the record is different than required
            quantity
        """

        self.compute_quantity()

        have = len(items)
        need = self.quantity
        skip = self.skip_faulty_lines

        msg = _('Template «{} ({})»: There are not enough questions ({}/{})')
        msg = msg.format(self.name, self.id, have, need)

        if not ((skip and have > 0) or (have == need)):
            raise UserError(msg)

    def _begin_proccess(self):
        """ Turns off the autocommit

        Returns:
            bool -- Always returns False. This value can be used as success.
        """

        self.env.cr.autocommit(False)

        return False

    def _end_proccess(self, success=True):
        """ Commit or rollback transaction and after it turns on autocommit

        Keyword Arguments:
            success {bool} -- True to perform acommit (default: {True})

        Returns:
            bool -- returns the given success value
        """

        if success:
            self.env.cr.commit()
        else:
            self.env.cr.rollback()

        self.env.cr.autocommit(True)

        return success

    @staticmethod
    def safe_cast(val, to_type, default=None):
        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default

    def _get_field_id(self, fname):
        item = getattr(self, fname)

        return item.id if item else None

    @staticmethod
    def _has_flag(value, flag):
        return value & flag == flag

    def _get_test_info(self, overwrite, test_id=None):
        """ Get information will be writed in test record

        @param test_id (models.Model): single test record
        @param overwrite (int): bit field at C style

        |     4     |     2     |     1     |  0   |
        | --------- | --------- | --------- | ---- |
        | Test info | Questions | Overwrite | None |

        """

        values = {}

        overwrite_info = self._has_flag(overwrite, OverwriteInfo.TESTINFO)

        if overwrite_info or not test_id:
            res_id = self._get_field_id('correction_scale_id')
            values['correction_scale_id'] = res_id

        if overwrite_info or not test_id:
            res_id = self._get_field_id('test_kind_id')
            values['test_kind_id'] = res_id

        if overwrite_info or not test_id:
            values['preamble'] = self.preamble

        if overwrite_info or not test_id:
            values['description'] = self.test_description

        if overwrite_info or not test_id:
            values['time_by'] = self.time_by

        if overwrite_info or not test_id:
            values['available_time'] = self.available_time

        if overwrite_info:
            values['lock_time'] = self.lock_time

        return values

    def _new_name(self, extra=None):
        now = datetime.now()
        pattern = self.name_pattern

        if pattern.find('{sequence}') >= 0:
            sequence = 'academy_tests.ir_sequence_academy_tests_test'
            sequence = self.env.ref(sequence)
            sequence = sequence.next_by_id()
        else:
            sequence = None

        pattern = pattern.format(
            template=self.name,
            owner=self.owner_id.name or _('ownerless'),
            scale=self.correction_scale_id.name or _('default'),
            kind=self.test_kind_id.name or _('common'),
            sequence=sequence,
            extra=extra
        )

        pattern = now.strftime(pattern)

        return pattern

    def _original_template_id(self):
        """ Check if self is child of another template and returns:
        a) If this is a child template, the parent template ID
        b) If this is not a child template, the own ID

        Returns:
            int -- parent ID if exists or self ID
        """

        return self.parent_id.id if self.parent_id else self.id

    def _append_questions(self, test_id, overwrite, context_ref):
        self.ensure_one()

        question_set = self.env['academy.tests.question']
        values = self._get_test_info(overwrite, test_id=test_id)

        question_ids = self._exclude_incremental()
        if question_ids:
            domain = [('id', 'not in', question_ids)]
        else:
            domain = []

        overwrite = self._has_flag(overwrite, OverwriteInfo.QUESTIONS)
        if test_id.question_ids and not overwrite:
            ids = test_id.question_ids.mapped('question_id.id')
            domain.extend([('id', 'not in', ids)])
            values['question_ids'] = []
        else:
            values['question_ids'] = [(5, 0, 0)]
            values['random_template_id'] = self._original_template_id()

        # question_set = self.random_line_ids.perform_search(
        #     domain, context_ref, self.skip_faulty_lines)

        link_values = self.random_line_ids.build_link_operations(
            domain, context_ref, self.skip_faulty_lines)

        self.assert_expected_questions(link_values)
        self.assert_no_more_than_required(link_values)

        # link_values = self._build_link_operations(question_set)
        values['question_ids'].extend(link_values)

        test_id.write(values)

        return question_set

    def append_questions(self, test_id, overwrite=False, context_ref=None):
        """ Calls action by each related line
        """
        question_set = self.env['academy.tests.question']
        overwrite = self.safe_cast(overwrite, int, 0)

        success = self._begin_proccess()

        try:
            for record in self:
                question_set += record._append_questions(
                    test_id, overwrite, context_ref)

            success = True

        except UserError as error:
            raise error

        except Exception as ex:
            _logger.error(ex)
            raise UserError(_('A serious error has occurred, check log files'))

        self._end_proccess(success)

        return question_set

    def _build_link_operations(self, question_set):
        operations = []

        request_id = self.env.context.get('request_id', None)

        sequence = 10
        for question_item in question_set:
            link = {
                'sequence': sequence,
                'question_id': question_item.id,
                'request_id': request_id
            }
            operations.append((0, None, link))
            sequence += 10

        return operations

    def assert_no_more_than_required(self, items):
        msg = _('Too many questions supplied {}/{}')

        request_id = self.env.context.get('request_id', False)

        if request_id:
            domain = [('id', '=', request_id)]
            request_set = self.env['academy.tests.question.request']
            result = request_set.search_read(domain, ['maximum'])

            if result:
                if(len(items) > result[0]['maximum']):
                    msg = msg.format(len(items), result[0]['maximum'])
                    raise UserError(msg)

    def _new_test(self, context_ref):
        self.ensure_one()

        test_id = None
        allow_partial = self.skip_faulty_lines

        # question_set = self.random_line_ids.perform_search(
        #     context_ref=context_ref, allow_partial=self.skip_faulty_lines)

        values = self._get_test_info(overwrite=OverwriteInfo.ALL, test_id=None)
        values['name'] = self._new_name()
        values['random_template_id'] = self._original_template_id()

        question_ids = self._exclude_incremental()
        if question_ids:
            domain = [('id', 'not in', question_ids)]
        else:
            domain = TRUE_DOMAIN

        # link_values = self._build_link_operations(question_set)
        values['question_ids'] = self.random_line_ids.build_link_operations(
            extra=domain, context_ref=context_ref, allow_partial=allow_partial)

        self.assert_expected_questions(values['question_ids'])
        self.assert_no_more_than_required(values['question_ids'])

        test_id = self.env['academy.tests.test']
        test_id = test_id.create(values)

        return test_id

    def new_test(self, gui=True, context_ref=None):
        """ Create a new test from template and attach it to the chosen context
        if it has been set.

        Keyword Arguments:
            context_ref {recordset} -- single action or enrolment will be used
            as context (default: {None})
            gui {bool} -- True to return an action to show the new created
            test (default: {True})

        Returns:
            mixed -- if gui is True then an Odoo action window to show new
            created test, otherwise the new created test

        Raises:
            error -- Unknown common exception, will be sent to log
            UserError -- The established restrictions cannot be satisfied
        """

        success = self._begin_proccess()
        test_id = self.env['academy.tests.test']

        if context_ref is None:  # But it's not False
            context_ref = self.context_ref

        try:

            for record in self:
                test_id = record._new_test(context_ref)

                if context_ref:
                    context_ref.test_ids = [(4, test_id.id, 0)]

            success = True

        except UserError as error:
            raise error

        except Exception as ex:
            _logger.error(ex)
            raise UserError(_('A serious error has occurred, check log files'))

        self._end_proccess(success)

        if gui and success and len(self) == 1:
            return self._show_test(test_id)
        else:
            return test_id

    def _show_test(self, test_item):
        """ Builds a form action to display a single test

        This will be used to show new created tests

        Arguments:
            test_item {recordset} -- single test recordset

        Returns:
            dict -- Odoo action window to show new tests
        """

        action = self.env.ref('academy_tests.action_tests_act_window')

        return {
            'name': action.name,
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': action.res_model,
            'res_id': test_item.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': action.domain,
            'context': action.context,
        }

    def view_tests(self):
        """ Builds a tree action to display all tests have been created with
        this single template

        This will be used by a smart button existing on the template form view

        Arguments:
            test_item {recordset} -- single test recordset

        Returns:
            dict -- Odoo action window to show created tests
        """

        self.ensure_one()

        xid = 'academy_tests.action_tests_act_window'
        action = self.env.ref(xid)

        test_ids = self.mapped('test_ids.id')
        domain = eval_domain(action.domain)

        return {
            'name': _('Tests made with «{}»').format(self.name),
            'view_mode': action.view_mode,
            'view_id': False,
            'view_type': 'tree',
            'res_model': action.res_model,
            'res_id': None,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': AND([domain, [('id', 'in', test_ids)]]),
            'context': action.context,
            'limit': action.limit,
            'help': action.help,
            'view_ids': action.view_ids.mapped('id'),
            'views': action.views
        }

    def edit_lines(self):
        self.ensure_one()

        view_xid = 'academy_tests.view_academy_tests_random_line_editable_tree'

        return {
            'name': _('Lines in «{}»').format(self.name),
            'view_mode': 'tree',
            'view_id': self.env.ref(view_xid).id,
            'view_type': 'form',
            'res_model': 'academy.tests.random.line',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('random_template_id', '=', self.id)],
        }

    def _exclude_incremental(self):
        question_ids = []

        self.ensure_one()

        if self.incremental:

            test_obj = self.env['academy.tests.test']
            map_path = 'question_ids.question_id.id'
            domain = []

            if self.incremental in ['tpl', 'tplusr']:
                tplid = self._original_template_id()
                domain.append(('random_template_id', '=', tplid))

            if self.incremental in ['usr', 'tplusr']:
                uid = self.env.context.get('uid', False)
                domain.append(('owner_id', '=', uid))

            test_set = test_obj.search(domain)
            question_ids = test_set.mapped(map_path)

        return question_ids
