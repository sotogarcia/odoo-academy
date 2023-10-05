# -*- coding: utf-8 -*-
""" AcademyTestsRandomTemplate

This module contains the academy.tests.random.templeate Odoo model which stores
all academy tests random templeate attributes and behavior.
"""


from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.osv.expression import AND

from .utils.libuseful import eval_domain
from odoo.addons.academy_base.models.academy_abstract_training \
    import AcademyAbstractTraining

from enum import IntFlag
from datetime import datetime
from dateutil.relativedelta import relativedelta
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

    _inherit = [
        'academy.abstract.training.reference',
        'ownership.mixin',
        'image.mixin',
        'mail.thread'
    ]

    _rec_name = 'name'
    _order = 'name ASC'
    _check_company_auto = True

    company_id = fields.Many2one(
        string='Company',
        required=False,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help='The company this record belongs to',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_company_id',
        store=True
    )

    @api.depends('training_ref')
    def _compute_company_id(self):
        for record in self:
            training_ref = record.training_ref
            if training_ref and hasattr(training_ref, 'company_id'):
                record.company_id = getattr(training_ref, 'company_id', None)
            else:
                record.company_id = None

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

    test_count = fields.Integer(
        string='Nº of tests',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of test have been created using this template',
        compute='_compute_test_count'
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Maximum number of questions can be appended',
        compute='_compute_quantity',
        wizard=True,
        store=False,
    )

    lines_count = fields.Integer(
        string='Nº lines',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of lines',
        store=False,
        compute='_compute_line_count'
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
        store=False,
        help='Show number of scheduled tasks',
        compute='_compute_scheduled_count'
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
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_test_kind_id(),
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
        default=lambda self: self.default_preamble(),
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
        size=1024,
        translate=True,
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

    serial = fields.Integer(
        string='Serial',
        required=True,
        readonly=True,
        index=False,
        default=1,
        help='Number of test have been created using this template'
    )

    self_assignment = fields.Boolean(
        string='Self assignment',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to self assign template to new created test',
    )

    # ----------------- AUXILIARY FIELDS METHODS AND EVENTS -------------------

    @api.depends('test_ids')
    def _compute_test_count(self):
        for record in self:
            record.test_count = len(record.test_ids)

    @api.depends('scheduled_ids')
    def _compute_scheduled_count(self):
        for record in self:
            record.scheduled_count = len(record.scheduled_ids)

    @api.onchange('training_ref')
    def _onchange_training_ref(self):
        default_scale = self.default_correction_scale_id()

        for record in self:
            training = record.training_ref

            if training and hasattr(training, 'correction_scale_id'):
                record.correction_scale_id = training.correction_scale_id
            else:
                record.correction_scale_id = default_scale

    @api.onchange('scheduled_ids')
    def _onchange_scheduled_ids(self):
        self._compute_scheduled_count()

    def default_test_kind_id(self):
        return self.env.ref('academy_tests.academy_tests_test_kind_common')

    def default_preamble(self):
        return self.env['academy.tests.test'].default_preamble()

    def default_correction_scale_id(self):
        xid = 'academy_tests.academy_tests_correction_scale_default'
        result = self.env.ref(xid)

        return result.id if result else None

    @api.depends('random_line_ids')
    def _compute_quantity(self):
        """ This computes lines_count field """
        for record in self:
            values = record.random_line_ids.mapped('quantity')
            record.quantity = sum(values)

    @api.depends('random_line_ids')
    def _compute_line_count(self):
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

    # ---------------------------- PUBIC METHODS ------------------------------

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
            res_id = self._get_field_id('test_kind_id')
            values['test_kind_id'] = res_id

        if overwrite_info or not test_id:
            values['preamble'] = self.preamble

        if overwrite_info or not test_id:
            values['description'] = self.test_description

        return values

    def _get_name_uid(self):
        """ Gets the name of the active user will be used to use to generate
        new test names
        """

        uid = self.env.context.get('uid', -1)
        user = self.env['res.users'].search([('id', '=', uid)], limit=1)
        return user.name or _('authorless')

    def _get_training_name(self):
        """ Gets the name of the related training item will be used to use to
        generate new test names
        """

        if self.training_ref:
            result = self.training_ref.get_name()
        else:
            result = _('global')

        return result

    def _new_name(self, extra=None):
        """Makes a new test name according to the pattern supplied by user

        Args:
            extra (str, optional): some extra text can be used as a part of the
            new test name

        Returns:
            str: new generated test name
        """

        now = datetime.now()
        pattern = self.name_pattern

        # Fills {template}, {owner}, {scale},...
        pattern = pattern.format(
            template=self.name,
            owner=self.owner_id.name or _('ownerless'),
            scale=self.correction_scale_id.name or _('default'),
            kind=self.test_kind_id.name or _('common'),
            sequence=self.serial,
            extra=extra,
            uid=self._get_name_uid(),
            training=self._get_training_name()
        )

        # Fills any valid pattern for strftime
        name = now.strftime(pattern)

        # Truncate and capitalize first letter
        if name:
            name = name[:255]
            name = name[0].upper() + name[1:]

        return name

    def _original_template_id(self):
        """ Check if self is child of another template and returns:
        a) If this is a child template, the parent template ID
        b) If this is not a child template, the own ID

        Returns:
            int -- parent ID if exists or self ID
        """

        return self.parent_id.id if self.parent_id else self.id

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

        return [('id', 'not in', question_ids)] if question_ids else []

    @staticmethod
    def _accumulate_domain(base_domain, accumulate_ids):
        if accumulate_ids:
            domain = AND([base_domain, [('id', 'not in', accumulate_ids)]])
        else:
            domain = base_domain.copy()

        return domain

    @staticmethod
    def append_links(m2m_operations, line, question_set, sequence):
        request_id = line.env.context.get('request_id', None)

        if line.test_block_id:
            test_block_id = line.test_block_id.id
        else:
            test_block_id = None

        for question in question_set:
            link = {
                'sequence': sequence,
                'question_id': question.id,
                'request_id': request_id,
                'test_block_id': test_block_id
            }
            m2m_operations.append((0, None, link))

    def _compute_correction_scale(self):
        """ The correction scale can come from template, related training or
        default correction scale

        Returns:
            record: correction scale single item
        """

        correction_scale = self.correction_scale_id

        if not correction_scale:
            correction_scale = self.training_ref.correction_scale_id

        if not correction_scale:
            xid = 'academy_tests.academy_tests_correction_scale_default'
            correction_scale = self.env.ref(xid)

        return correction_scale

    def _assign(self, test_id):
        self.ensure_one()

        correction_scale = self._compute_correction_scale()

        values = {
            'name': test_id.name,
            'active': True,
            'test_id': test_id.id,
            'owner_id': self.owner_id.id,
            'training_ref': self.training_ref.get_reference(),
            'random_template_id': self.id,
            'secondary_id': None,
            'release': fields.Datetime.now(),
            'expiration': fields.Datetime.now() + relativedelta(years=100),
            'correction_scale_id': correction_scale.id,
            'time_by': getattr(self, 'time_by', 'test'),
            'available_time': getattr(self, 'available_time', '0.5'),
            'lock_time': getattr(self, 'lock_time', True)
        }

        assignment_obj = self.env['academy.tests.test.training.assignment']
        return assignment_obj.create(values)

    @staticmethod
    def assert_expected_questions(line, record_set):
        msg = _('RANDOM WIZARD LINE «{}»: There is not enough questions')

        allow_partial = line.random_template_id.skip_faulty_lines
        if not allow_partial and len(record_set) != line.quantity:
            raise UserError(msg.format(line.name))

    def _append_questions(self, test_id, overwrite):
        self.ensure_one()

        question_set = self.env['academy.tests.question']

        base_domain = self._exclude_incremental()
        values = self._get_test_info(overwrite, test_id=test_id)

        overwrite = self._has_flag(overwrite, OverwriteInfo.QUESTIONS)
        if test_id.question_ids and not overwrite:
            ids = test_id.question_ids.mapped('question_id.id')
            base_domain.extend([('id', 'not in', ids)])
            values['question_ids'] = []
        else:
            values['question_ids'] = [(5, 0, 0)]
            values['random_template_id'] = self._original_template_id()

        sequence = 0
        m2m_operations = []
        accumulate_ids = []

        for line in self.random_line_ids:
            sequence = sequence + 10

            domain = self._accumulate_domain(base_domain, accumulate_ids)

            question_set = line.perform_search(domain)
            self.assert_expected_questions(line, question_set)

            self.append_links(m2m_operations, line, question_set, sequence)
            accumulate_ids.extend(question_set.mapped('id'))

        values['question_ids'].extend(m2m_operations)
        test_id.write(values)

        return question_set

    def append_questions(self, test_id, overwrite=False):
        """ Try to append existing questions to a given test using
        template criteria

        Args:
            test_id: test ID or single recordset
            overwrite (OverwriteInfo): elements will be overwritten

        Returns:
            recordset: questions have been added to the test

        Raises:
            error -- Unknown common exception, will be sent to log
            UserError -- The established restrictions cannot be satisfied
        """

        question_set = self.env['academy.tests.question']
        overwrite = self.safe_cast(overwrite, int, 0)

        if isinstance(test_id, int):
            test_id = self.env.browse(test_id)

        success = self._begin_proccess()

        try:
            for record in self:
                question_set += record._append_questions(test_id, overwrite)

            success = True

        except UserError as error:
            raise error

        except Exception as ex:
            _logger.error(ex)
            raise UserError(_('A serious error has occurred, check log files'))

        self._end_proccess(success)

        return question_set

    def _new_test(self, name=False):
        self.ensure_one()

        test = self.env['academy.tests.test']

        base_domain = self._exclude_incremental()

        values = self._get_test_info(overwrite=OverwriteInfo.ALL)
        values['name'] = name or self._new_name()
        values['random_template_id'] = self._original_template_id()
        values['test_kind_id'] = self.test_kind_id.id

        sequence = 0
        m2m_operations = []
        accumulate_ids = []

        for line in self.random_line_ids:
            sequence = sequence + 10

            domain = self._accumulate_domain(base_domain, accumulate_ids)

            question_set = line.perform_search(domain)
            self.assert_expected_questions(line, question_set)

            self.append_links(m2m_operations, line, question_set, sequence)
            accumulate_ids.extend(question_set.mapped('id'))

        values['question_ids'] = m2m_operations
        test_id = test.create(values)

        self.serial = self.serial + 1

        if self.self_assignment and self.training_ref:
            self._assign(test_id)

        return test_id

    def new_test(self, gui=True, training_ref=None, name=False):
        """ Create a new test from template and attach it to the chosen context
        if it has been set.

        Keyword Arguments:
            training_ref {recordset} -- single action or enrolment will be used
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

        try:

            for record in self:
                test_id = record._new_test(name)

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

    # -------------------- CREATE NEW TEMPLATE FROM TRAINIG -------------------

    @staticmethod
    def _search_for_activity(training):

        # Try to find a related training activity
        if hasattr(training, 'training_activity_id'):
            activity = training.training_activity_id
        else:
            path = training.get_path_down('academy.training.activity')
            activity = training.mapped(path) if path is not False else False

        return activity

    @api.model
    def _compute_template_name(self, training=False):
        training_name = training.get_name()

        uid = training._context.get('uid', self.env.ref('base.user_root').id)
        user = self.env['res.users'].browse(uid)

        pattern = '{} - {} - {}'

        name = pattern.format(user.name, training_name, '%')
        domain = [('name', 'ilike', name)]
        num = self.env[self._name].search_count(domain) + 1

        return pattern.format(user.name, training_name, num + 1)

    @api.model
    def _compute_template_values(self, training, name=False):
        values = dict(
            name=name or self._compute_template_name(training),
            description=None,
            active=True,
            random_line_ids=[(5, None, None)],
            correction_scale_id=self.default_correction_scale_id()
        )

        if training:
            values['training_ref'] = training.get_reference()

            activity = self._search_for_activity(training)
            if activity:
                values['available_time'] = activity.available_time

                scale_id = activity.correction_scale_id
                if scale_id:
                    values['correction_scale_id'] = scale_id.id

        return values

    def _line_default_question_type(self):
        theoretical_id = None

        try:
            theoretical_xid = 'academy_tests.academy_tests_question_type_1'
            theoretical_id = self.env.ref(theoretical_xid).id
        except Exception as ex:
            _logger.debug(ex)

        return theoretical_id

    @api.model
    def _compute_line_values(self, name, quantity, previous=False):

        if previous and 'question_type' in previous.keys():
            question_type_id = previous.get('question_type')
        else:
            question_type_id = self._line_default_question_type()

        sequence = (previous.get('sequence', 0) if previous else 0) + 10

        return dict(
            random_template_id=None,
            name=name,
            description=None,
            active=True,
            sequence=sequence,
            quantity=quantity,
            type_ids=[(6, 0, [question_type_id])],
            authorship=None,
            exclude_tests=True,
            tests_by_context=True,
            categorization_ids=[(5, None, None)],
        )

    @staticmethod
    def _search_for_competencies(training, competency_ids=None):

        # Try to find a related training competencies
        if hasattr(training, 'competency_unit_ids'):
            competency_set = training.competency_unit_ids
        else:
            path = training.get_path_down('academy.competency_unit_ids')
            if path is not False:
                competency_set = training.mapped(path)
            else:
                competency_set = False

        if competency_set and competency_ids:
            competency_set = competency_set.filtered(
                lambda x: x.id in competency_ids)

        return competency_set

    @api.model
    def _get_target_lines(self, training, extended=False, competency_ids=None):
        """
        """
        if extended:
            path = training.get_path_down()
            path = '.'.join([path, 'topic_link_ids'])
            record_set = training.mapped(path)
        else:
            record_set = \
                self._search_for_competencies(training, competency_ids)
            if not record_set:
                record_set = training

        return record_set

    @staticmethod
    def _categorization_values(link, previous=False):
        category_ids = link.mapped('category_ids.id')
        sequence = previous['sequence'] + 10 if previous else 10

        return dict(
            description=link.topic_id.name,
            active=True,
            sequence=sequence,
            topic_id=link.topic_id.id,
            topic_version_ids=[(6, None, [link.topic_version_id.id])],
            category_ids=[(6, None, category_ids)],
        )

    @staticmethod
    def _get_target_name_and_questions(target):
        if hasattr(target, 'topic_id'):
            name = target.topic_id.name
        else:
            name = target.get_name()

        quantity = getattr(target, 'number_of_questions', 2)

        return name, quantity

    def _read_supplementary_from_context(self):
        quantity = self.env.context.get('supplementary_quantity', 0)
        block_id = self.env.context.get('supplementary_block_id', None)

        return quantity, block_id

    def get_template_values(self, training, extended=False,
                            competency_ids=None):
        """ Create new template for an specific given training

        Args:
            training (academy.abstract.training): training item
            extended (bool, optional): True to make one line by each training
            module link or False to make one line by competency unit
            competency_ids (None, optional): limit new lines to specific
            competency units

        Returns:
            dict: values needed to invoke the create method for a new template
        """

        training.ensure_one()

        m2m_supplementary = [(5, 0, 0)]  # Optional supplementary line
        tvalues = self._compute_template_values(training)

        line_values = False
        target_set = self._get_target_lines(training, extended, competency_ids)

        for target in target_set:  # Targets can be a modules or links

            name, quantity = self._get_target_name_and_questions(target)

            line_values = self._compute_line_values(
                name, quantity, line_values)

            cvalues = False
            link_ids = getattr(target, 'topic_link_ids', target)
            for link in link_ids:
                cvalues = self._categorization_values(link, cvalues)
                m2m_categorization = (0, 0, cvalues)
                line_values['categorization_ids'].append(m2m_categorization)

                # Store it to allow to append an supplementary line later
                m2m_supplementary.append(m2m_categorization)

            m2m_line = (0, 0, line_values)
            tvalues['random_line_ids'].append(m2m_line)

        supplementary, block_id = self._read_supplementary_from_context()

        # There must be at least one line before the supplementary
        if supplementary > 0 and line_values:
            line_values = self._compute_line_values(
                _('Supplementary questions'), supplementary, line_values)

            line_values['test_block_id'] = block_id
            line_values['categorization_ids'] = m2m_supplementary

            m2m_line = (0, 0, line_values)
            tvalues['random_line_ids'].append(m2m_line)

        return tvalues

    def _with_normalized_context(self):
        expected = ['supplementary_quantity', 'supplementary_block_id']
        context = {k: v for k, v in self.env.context.items() if k in expected}
        return self.with_context(context)

    @api.model
    def template_for_training(self, training_ref, extended=False,
                              no_open=False, competency_ids=None):
        """ Create a new template based on given training (action, ...)
        This method will be called from JavaScript when user clics an extra
        button on the templeates LitsView header

        Args:
            training_ref (str): reference (model,id) to an elrollment
            training action, activity, competency unit or module
        """

        split_ref = AcademyAbstractTraining.split_reference
        model, _id = split_ref(training_ref)

        target = self.env[model].browse(_id)

        template_obj = self.env['academy.tests.random.template']

        _self = self._with_normalized_context()
        values = _self.get_template_values(
            target, extended, competency_ids)

        template = template_obj.create(values)

        if not no_open and template:
            return self._template_act_window(template)
        else:
            return template

    @staticmethod
    def _template_act_window(template):

        if not template:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Template',
            'res_model': 'academy.tests.random.template',
            'res_id': template.id,
            'views': [[False, 'form']],
            'target': 'main',
            'views': [[False, 'form']],
            'view_type': 'form',
            'view_mode': 'form',
            'flags': {
                'form': {
                    'action_buttons': True,
                    'options': {'mode': 'edit'}
                }
            }
        }

    # ---------------------------- BUTTON ACTIONS -----------------------------

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
