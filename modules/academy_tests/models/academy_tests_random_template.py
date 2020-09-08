# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Random Wizard Set

This module contains the academy.tests.random.wizard.Set an unique Odoo model
which contains all Academy Tests Random Wizard Set attributes and behavior.

This model is the representation of the real life academy tests random template

Classes:
    AcademyTestsRandomWizardSet: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

    Inside this class can be, in order, the following attributes and methods:
    * Object attributes like name, description, inheritance, etc.
    * Entity fields with the full definition
    * Computed fields and required computation methods
    * Events (@api.onchange) and other field required methods like computed
    domain, defaul values, etc...
    * Overloaded object methods, like create, write, copy, etc.
    * Public object methods will be called from outside
    * Private auxiliary methods not related with the model fields, they will
    be called from other class methods


Todo:
    * Complete the model attributes and behavior

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

from datetime import datetime

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestsRandomTemplate(models.Model):
    """ This model is the representation of the academy tests random template

    Fields:
      name (Char)       : Human readable name which will identify each record
      description (Text): Something about the record or other information which
      has not an specific defined field to store it.
      active (Boolean)  : Checked do the record will be found by search and
      browse model methods, unchecked hides the record.

    """


    _name = 'academy.tests.random.template'
    _description = u'Academy Tests Random Template'

    _inherit = ['image.mixin', 'mail.thread']

    _rec_name = 'name'
    _order = 'name ASC'


    name = fields.Char(
        string='Name',
        required=False,
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
        string='Lines',
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
        limit=None
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
        limit=None
    )


    owner_id = fields.Many2one(
        string='Owner',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_owner_id(),
        help='Current test owner',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        groups='academy_base.academy_group_technical',
        wizard=True
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
        help='Check to not allow the user to continue with the test once the time has passed',
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
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about the test',
        translate=True,
        wizard=True
    )

    single_transaction = fields.Boolean(
        string='Single transaction',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Perform all database actions in a single transaction',
        wizard=True
    )

    use_context = fields.Boolean(
        string='Use context',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Read some restriction (action/module) information from context',
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

    allow_automate = fields.Boolean(
        string='Allow automate',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to allow use this template in automatic tasks',
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
        translate=True
    )


    # ----------------- AUXILIARY FIELDS METHODS AND EVENTS -------------------

    def default_correction_scale_id(self):
        xid = 'academy_tests.academy_tests_correction_scale_default'
        result = self.env.ref(xid)
        print(result)
        return result.id if result else null

    def default_owner_id(self):
        uid = 1
        if 'uid' in self.env.context:
            uid = self.env.context['uid']

        return uid


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
            'sequence': sequence,
            'active': True
        }


    @staticmethod
    def _build_many2many_write_action(question_set, base_values):
        leafs = []
        values = base_values.copy()
        for question in question_set:
            values['question_id'] = question.id
            values['sequence'] = values['sequence'] + 1

            leafs.append((0, None, values.copy()))

        return leafs


    def _perform_many2many_write_action(self, leafs, test_id):
        return test_id.write({'question_ids': leafs})


    # ---------------------------- PUBIC METHODS ------------------------------

    def _process_line(self, line, test_id):
        question_set = self.env['academy.tests.question']

        try:

            # STEP 1: build skeleton dictionary with required values to create
            # new ``academy.tests.test.question.rel`` records
            sequence = self._compute_base_sequence_value(test_id)
            values = self._get_base_values(test_id, sequence)

            # STEP 2: build a domain to exclude existing questions
            # NOTE: Questions are linked to ``academy.tests.test.question.rel``
            exclusion_leafs = []
            if test_id.question_ids:
                qids = test_id.question_ids.mapped('question_id').mapped('id')
                exclusion_leafs.append(('id', 'not in', qids))

            # STEP 3: Performa search and return a set of questions
            question_set = line.perform_search(exclusion_leafs)

            # STEP 4: Link questions through many2many relation
            leafs = self._build_many2many_write_action(question_set, values)
            self._perform_many2many_write_action(leafs, test_id)

        except AssertionError as err:
            if self.skip_faulty_lines:
                msg = _('Line «{} ({})» has fail: {}')
                _logger.warning(msg.format(line.name, line.id, err))
            else:
                raise err

        # STEP 5: Return lines
        return question_set


    def assert_expected_questions(self, result_set):
        self.compute_quantity()

        have = len(result_set)
        need = self.quantity
        skip = self.skip_faulty_lines

        msg = _('Template «{} ({})»: There are not enough questions')
        msg = msg.format(self.name, self.id)

        assert (skip and have > 0) or (have == need), msg


    def _begin_append_proccess(self):
        if self.single_transaction:
            self._cr.autocommit(False)
        else:
            self._cr.autocommit(True)


    def _end_append_proccess(self, success=True):
        if self.single_transaction:
            if success:
                self._cr.commit()
            else:
                self._cr.rollback()

    @staticmethod
    def safe_cast(val, to_type, default=None):
        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default


    def _write_test_info(self, test_id, overwrite=False):
        """ Write test info, reset content or both

        @param test_id (models.Model): single test record
        @param overwrite (int): bit field at C style

        |     4     |     2     |     1     |  0   |
        | --------- | --------- | --------- | ---- |
        | Test info | Questions | Overwrite | None |

        """

        self.ensure_one()

        values = {}

        overwrite = self.safe_cast(overwrite, int, 0)
        overwrite_info = (overwrite and 4 == 4)
        overwrite_content = (overwrite and 2 == 2)

        if overwrite_info or not test_id.correction_scale_id:
            res_id = self.correction_scale_id
            values['correction_scale_id'] = res_id

        if overwrite_info or not test_id.test_kind_id:
            res_id = self.test_kind_id
            values['test_kind_id'] = res_id

        if overwrite_info or not test_id.preamble:
            values['preamble'] = self.preamble

        if overwrite_info or not test_id.description:
            values['description'] = self.test_description

        if overwrite_info or not test_id.time_by:
            values['time_by'] = self.time_by

        if overwrite_info or not test_id.available_time:
            values['available_time'] = self.available_time

        if overwrite_info:
            values['lock_time'] = self.lock_time

        if overwrite_content:
            values['question_ids'] = [(5, 0, 0)]

        if values:
            test_id.write(values)


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


    def append_questions(self, test_id, overwrite=False):
        """ Calls action by each related line
        """

        self.ensure_one()

        try:
            self._begin_append_proccess()

            result_set = self.env['academy.tests.question']

            self._write_test_info(test_id, overwrite)

            for line in self.random_line_ids:
                result_set += self._process_line(line, test_id)

            self.assert_expected_questions(result_set)

            self._end_append_proccess()

        except AssertionError as err:
            self._end_append_proccess(False)
            raise UserError(err)

        except:
            self._end_append_proccess(False)
            raise

        return result_set


    def _create_test(self):
        test_id=self.env['academy.tests.test']

        values = {
            'name': self._new_name(),
            'random_template_id': self.id
        }

        test_id = test_id.create(values)
        self.env.cr.commit()

        return test_id



    def populate_all(self):
        task_set = self.env['academy.random.template.scheduled.rel']
        test = self.env['academy.tests.test'].browse(714)

        for record in self:
            domain = [('random_template_id', '=', record.id)]
            task_set = task_set.search(domain)

            for task in task_set:
                ctx = dict(
                    active_model=task.model,
                    active_ids = [task.res_id],
                    student_ids=[task.student_id.id]
                )

                test_id = self._create_test()

                contextualized = self.with_context(ctx)
                result_set = contextualized.append_questions(test_id, True)

                task.enrolment_id.test_ids = [(4, test_id.id, 0)]


