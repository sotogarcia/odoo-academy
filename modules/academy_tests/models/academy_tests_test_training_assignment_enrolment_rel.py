# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.exceptions import AccessError, ValidationError
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.addons.academy_base.utils.record_utils \
    import create_domain_for_ids as make_domain

from logging import getLogger
from psycopg2 import Error as Psycopg2Error
from psycopg2.errors import SerializationFailure
from datetime import time, datetime, timedelta
from time import sleep


_logger = getLogger(__name__)

MAX_RETRIES = 5

_ENROLMENT_AVAILABLE_ASSIGNMENT_REL = '''
WITH training_enrolments AS (
    SELECT DISTINCT
        tta."id" AS assignment_id,
        tae."id" AS enrolment_id
    FROM
        academy_tests_test_training_assignment AS tta
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae."id" = tta.enrolment_id
    {join} {where}
), training_actions AS (
    SELECT DISTINCT
        tta."id" AS assignment_id,
        tae."id" AS enrolment_id
    FROM
        academy_tests_test_training_assignment AS tta
    INNER JOIN academy_training_action AS ata
        ON ata."id" = tta.training_action_id AND ata.active
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = ata."id"
    {join} {where}
), training_activities AS (
    SELECT DISTINCT
        tta."id" AS assignment_id,
        tae."id" AS enrolment_id
    FROM
        academy_tests_test_training_assignment AS tta
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = tta.training_activity_id AND atc.active
    INNER JOIN academy_training_action AS ata
        ON ata.training_activity_id = atc."id" AND ata.active
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = ata."id"
    {join} {where}
), competency_units AS (
    SELECT DISTINCT
        tta."id" AS assignment_id,
        tae."id" AS enrolment_id
    FROM
        academy_tests_test_training_assignment AS tta
    INNER JOIN academy_competency_unit AS acu
        ON acu."id" = tta.competency_unit_id AND acu.active
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = acu.training_activity_id AND atc.active
    INNER JOIN academy_training_action AS ata
        ON ata.training_activity_id = atc."id" AND ata.active
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = ata."id"
    {join} {where}
), training_modules AS (
    SELECT DISTINCT
        tta."id" AS assignment_id,
        tae."id" AS enrolment_id
    FROM
        academy_tests_test_training_assignment AS tta
    INNER JOIN academy_training_module AS atm
        ON atm."id" = tta.training_module_id AND atm.active
        AND atm.training_module_id IS NULL
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm."id" AND acu.active
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = acu.training_activity_id AND atc.active
    INNER JOIN academy_training_action AS ata
        ON ata.training_activity_id = atc."id" AND ata.active
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = ata."id"
    {join} {where}
), training_units AS (
    SELECT DISTINCT
        tta."id" AS assignment_id,
        tae."id" AS enrolment_id
    FROM
        academy_tests_test_training_assignment AS tta
    INNER JOIN academy_training_module AS atu
        ON atu."id" = tta.training_module_id  AND atu.active
        AND atu.training_module_id IS NOT NULL
    INNER JOIN academy_training_module AS atm
        ON atm."id" = atu.training_module_id AND atm.active
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm."id" AND acu.active
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = acu.training_activity_id AND atc.active
    INNER JOIN academy_training_action AS ata
        ON ata.training_activity_id = atc."id" AND ata.active
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = ata."id"
    {join} {where}
)
SELECT
    training_enrolments.assignment_id,
    training_enrolments.enrolment_id
FROM
    training_enrolments UNION
SELECT
    training_actions.assignment_id,
    training_actions.enrolment_id
FROM
    training_actions UNION
SELECT
    training_activities.assignment_id,
    training_activities.enrolment_id
FROM
    training_activities UNION
SELECT
    competency_units.assignment_id,
    competency_units.enrolment_id
FROM
    competency_units UNION
SELECT
    training_modules.assignment_id,
    training_modules.enrolment_id
FROM
    training_modules
'''


# academyTrainingActionEnrolmentAvailableAssignmentRel
# academy.training.action.enrolment.available.assignment.rel
# academy_training_action_enrolment_available_assignment_rel


class AcademyTestsTestTrainingAssignmentEnrolmentRel(models.Model):
    """
    This model represents a relationship between test-training assignments and
    training action enrolments. It serves as a junction table that maps each
    enrolment to one or more assignments, enabling the tracking of which tests
    are assigned to which training enrolments in the context of an educational
    or training academy.
    """

    _name = 'academy.tests.test.training.assignment.enrolment.rel'
    _description = 'Individual test assignment'

    _table = 'academy_tests_test_training_assignment_enrolment_rel'

    _rec_name = 'id'
    _order = 'id DESC'

    _check_company_auto = True

    _max_allowed_errors = 10

    assignment_id = fields.Many2one(
        string='Assignment',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help=('This field links to the test-training assignment that this '
              'enrolment is related to.'),
        comodel_name='academy.tests.test.training.assignment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    # Updated by fast_update
    question_count = fields.Integer(
        string='Question count',
        required=True,
        readonly=True,
        index=True,
        default=0
    )

    # Updated by fast_update
    max_points = fields.Float(
        string='Max points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='The maximum points achievable in an attempt'
    )

    # Updated by fast_update
    date_start = fields.Datetime(
        string='Start date',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Date and time from which the assigned test becomes available',
    )

    # Updated by fast_update
    date_stop = fields.Datetime(
        string='Stop date',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Date and time at which the assigned test expires',
    )

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help=('This field links to the training action enrolment that is '
              'associated with a particular assignment.'),
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    company_id = fields.Many2one(
        string='Company',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Available for company',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='enrolment_id.company_id',
        store=True
    )

    # TODO: remove it
    student_id = fields.Many2one(
        string='Student',
        readonly=True,
        index=True,
        store=True,
        related='enrolment_id.student_id',
        help='References the student associated with this enrolment.',
        search='_search_student_id'
    )

    @api.model
    def _search_student_id(self, operator, value):
        domain = ['student_id', operator, value]
        enrolment_obj = self.env['academy.training.action.enrolment']
        enrolment_set = enrolment_obj.search(domain)

        enrolment_ids = enrolment_set.ids
        result_domain = [('enrolment_id', 'in', enrolment_ids)]

        return result_domain if enrolment_ids else FALSE_DOMAIN

    first_attempt_id = fields.Many2one(
        string='First attempt',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=('Reference to the first attempt at the assigned test for this '
              'enrolment.'),
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    last_attempt_id = fields.Many2one(
        string='Last attempt',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=('Reference to the most recent attempt at the assigned test for '
              'this enrolment.'),
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    best_attempt_id = fields.Many2one(
        string='Best attempt',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=('Reference to the highest scoring attempt at the assigned test '
              'for this enrolment.'),
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    first_attempt = fields.Datetime(
        string='First attempt datetime',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date and time when the first attempt was completed'
    )

    last_attempt = fields.Datetime(
        string='Last attempt datetime',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date and time when the last attempt was completed'
    )

    best_attempt = fields.Datetime(
        string='Best attempt datetime',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date and time when the best attempt was completed'
    )

    first_points = fields.Float(
        string='First points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Points earned on the first attempt'
    )

    last_points = fields.Float(
        string='Last points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Points earned on the last attempt'
    )

    best_points = fields.Float(
        string='Best points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Points earned on the best attempt'
    )

    attempt_ids = fields.One2many(
        string='Attempts',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.attempt',
        inverse_name='individual_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    # Will be filled by fast_update_attempt_data method
    attempt_count = fields.Integer(
        string='Attempt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=('Total number of attempts related to the current individual'
              'assignment.')
    )

    max_final_points = fields.Float(
        string='MAX final points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Maximum of points from final answers in the attempts of this '
              'assignment')
    )

    min_final_points = fields.Float(
        string='MIN final points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Minimum of points from final answers in the attempts of this '
              'assignment')
    )

    avg_final_points = fields.Float(
        string='AVG final points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from final answers in the attempts of this '
              'assignment')
    )

    avg_right_points = fields.Float(
        string='AVG right points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from right answers in the attempts of this '
              'assignment')
    )

    avg_wrong_points = fields.Float(
        string='AVG wrong points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from wrong answers in the attempts of this '
              'assignment')
    )

    avg_blank_points = fields.Float(
        string='AVG blank points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from blank answers in the attempts of this '
              'assignment')
    )

    avg_answered_count = fields.Integer(
        string='AVG answered count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of answered questions in the attempts of this '
              'assignment')
    )

    avg_right_count = fields.Integer(
        string='AVG right count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of right answers in the attempts of this '
              'assignment')
    )

    avg_wrong_count = fields.Integer(
        string='AVG wrong count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of wrong answers in the attempts of this '
              'assignment')
    )

    avg_blank_count = fields.Integer(
        string='AVG blank count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of blank questions in the attempts of this '
              'assignment')
    )

    passed_count = fields.Integer(
        string='Passed count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Number of passed attempts')
    )

    failed_count = fields.Integer(
        string='Failed count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Number of failed attempts')
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'assign_enrol_unique',
            'UNIQUE(assignment_id, enrolment_id)',
            _('Each assignment-enrolment pair must be unique.')
        )
    ]

    # -------------------------------------------------------------------------
    # Overridden Non-CRUD Methods
    # -------------------------------------------------------------------------

    def name_get(self):
        result = []

        for record in self:
            assignment = record.assignment_id.name or _('Unknown')
            student = record.student_id.name or _('Unknown')
            name = f'{assignment} - {student}'

            result.append((record.id, name))

        return result

    # -------------------------------------------------------------------------
    # CRUD Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def _prevent_update_attempt_data(vals_list):
        fields = ['first_attempt_id', 'last_attempt_id', 'best_attempt_id',
                  'first_attempt', 'last_attempt', 'best_attempt',
                  'first_points', 'last_points', 'best_points',
                  'attempt_count']

        if vals_list and isinstance(vals_list, (list, dict)):
            if isinstance(vals_list, (dict)):
                vals_list = [vals_list]

            for values in vals_list:
                for field in fields:
                    values.pop(field, None)

    @api.model_create_multi
    def create(self, vals_list):
        """ Overridden method 'create'
        """
        # If attempts related to them are created, modified, or deleted
        # they will invoke the method fast_update_attempt_data
        # self._prevent_update_attempt_data(vals_list)

        parent = super(AcademyTestsTestTrainingAssignmentEnrolmentRel, self)
        result = parent.create(vals_list)

        return result

    def write(self, values):
        """ Overridden method 'write'
        """
        # If attempts related to them are created, modified, or deleted
        # they will invoke the method fast_update_attempt_data
        # self._prevent_update_attempt_data(values)

        parent = super(AcademyTestsTestTrainingAssignmentEnrolmentRel, self)
        result = parent.write(values)

        return result

    # -------------------------------------------------------------------------
    # RECONCILE RECORDS
    # -------------------------------------------------------------------------

    @staticmethod
    def _read_ids(ids):
        """
        Converts input into a comma-separated string of IDs suitable for SQL
        queries.

        Args:
            ids (int, models.Model, tuple, list): The IDs to be converted.

        Returns:
            str: Comma-separated string of IDs.

        Raises:
            UserError: If the input type is not int, models.Model, tuple, or
            list.
        """
        if isinstance(ids, int):
            ids = [ids]
        elif isinstance(ids, models.Model):
            ids = ids.ids
        elif isinstance(ids, (tuple, list)):
            pass
        else:
            raise UserError(f'_join_ids({ids}): invalid type of argument.')

        return ','.join([str(item) for item in ids])

    @api.model
    def _get_max_allowed_errors(self):
        """
        Retrieves the maximum number of allowed errors from the model's
        attribute. This value is currently stored as an attribute of the model
        but may be transitioned to be managed via Odoo's ir.parameter for
        enhanced configurability in the future. This approach would allow
        system administrators to adjust the threshold directly from the Odoo
        configuration interface without needing to modify the code.

        Returns:
            int: The maximum number of allowed errors.

        Note:
            Transitioning to ir.config_parameter would provide a more flexible
            and user-friendly method for managing system parameters, supporting
            easier adjustments and better integration with Odoo's general
            configuration practices.
        """
        return self._max_allowed_errors

    @staticmethod
    def _error_limit_exceeded(errors, allowed, log_method='error'):
        """
        Checks if the number of errors exceeds the allowed limit and logs the
        error.

        Args:
            errors (int): The current number of errors.
            allowed (int): The maximum number of allowed errors.
            log_method (str): The logging method from the logger to use.

        Returns:
            bool: True if the error limit is exceeded, otherwise False.

        Raises:
            UserError: If the specified logging method does not exist.
        """

        result = False

        if errors > allowed:
            result = True
            if log_method:
                method = getattr(_logger, log_method, None)
                if not method:
                    message = f'Logging method "{log_method}" is not valid.'
                    raise UserError(message)

                message = f'Too many consecutive errors {errors} ' \
                          f'in the generate_missing_records method'
                method(message)

        return result

    @api.model
    def _execute_query(self, sql, selection=False, notify=False, action=None):
        results = []
        action = action or 'SQL'

        for attempt in range(MAX_RETRIES):
            try:
                cursor = self.env.cr
                cursor.execute(sql)

                if selection:
                    results = cursor.dictfetchall()

                break

            except SerializationFailure:
                if attempt < MAX_RETRIES - 1:
                    message = 'Failed to execute SQL {} / {} tries'
                    _logger.warning(message.format(attempt, MAX_RETRIES))
                    sleep(1)  # Wait before retry
                else:
                    if notify:
                        message = _('Failed to execute {} after {} tries')
                        raise UserError(message.format(action, MAX_RETRIES))
                    else:
                        message = 'Failed to execute {} after {} tries'
                        _logger.error(message.format(action, MAX_RETRIES))

            except Exception as ex:
                if notify:
                    message = _('Failed to execute {}. System says: {}')
                    raise UserError(message.format(action, ex))
                else:
                    message = 'Failed to execute {}. System says: {}'
                    _logger.error(message.format(action, ex))

                break

        return results if selection else True

    @api.model
    def _build_obsolete_records_sql(self, assignments=None, enrolments=None):
        """
        Constructs SQL to retrieve obsolete records based on the specified
        assignments and enrolments.

        Args:
            assignments (list, optional): List of assignment IDs to filter by.
            enrolments (list, optional): List of enrolment IDs to filter by.

        Returns:
            str: A SQL query string for fetching missing records.

        This method constructs a RIGHT JOIN SQL query to identify existing
        records without any existing related assignment or enrolment.
        """
        pattern = _ENROLMENT_AVAILABLE_ASSIGNMENT_REL

        join = '''
            RIGHT JOIN {table} AS rel
                ON rel.assignment_id = tta."id"
                AND rel.enrolment_id = tae."id"
        '''.format(table=self._table)

        where = 'WHERE rel."id" IS NOT NULL'

        if assignments:
            assignments = self._read_ids(assignments)
            where += f' AND tta."id" IN ({assignments})'

        if enrolments:
            enrolments = self._read_ids(enrolments)
            where += f' AND tae."id" IN ({enrolments})'

        return pattern.format(join=join, where=where)

    @api.model
    def purge_obsolete_records(self, assignments=None, enrolments=None):
        """
        Purges obsolete records from the database that meet specified criteria
        for assignments and enrolments. This method is primarily used to ensure
        data cleanliness and integrity, although in typical scenarios, the
        'ondelete='cascade'' attribute on 'assignment_id' and 'enrolment_id'
        relationships should automatically handle the deletion of obsolete
        records.
        This method was implemented to address specific edge cases where
        automatic cascading might not catch all necessary deletions, or where
        database integrity might have been compromised by previous data
        manipulations or migrations.

        Args:
            assignments (list, optional): List of assignment IDs to include in
                                          the search.
            enrolments (list, optional): List of enrolment IDs to include in
                                         the search.

        The method executes a RIGHT JOIN SQL query to find records linked to
        the specified assignments and enrolments that are no longer valid and
        should be purged.
        """
        sql = self._build_obsolete_records_sql(assignments, enrolments)
        results = self._execute_query(
            sql, selection=True, action='purge_obsolete_records'
        )

        if results:
            assignment_ids = [result['assignment_id'] for result in results]
            assignment_set = self.browse(assignment_ids)
            assignment_set.unlink()

    @api.model
    def _try_to_create_new(self, values):
        """
        Attempts to create a new record in the database with the given values.

        Args:
            values (dict): The values to use for creating the record.

        Returns:
            Model: The newly created record, or the model instance if creation
                   fails.

        Logs a warning with details of any exceptions encountered.
        """
        message = 'Error on create a new %s record with values %s. ' \
                  'System says: %s'
        try:
            result = self.create(values)
        except Exception as ex:
            data = (self._name, values, ex)
            _logger.warning(message % data)
            result = self.env[self._name]

        return result

    @api.model
    def _build_missing_records_sql(self, assignments=None, enrolments=None):
        """
        Constructs SQL for fetching records that are missing based on the
        specified assignments and enrolments.

        Args:
            assignments (list, optional): List of assignment IDs to filter by.
            enrolments (list, optional): List of enrolment IDs to filter by.

        Returns:
            str: A SQL query string for fetching missing records.

        This method constructs a LEFT JOIN SQL query to identify gaps in the
        records.
        """
        pattern = _ENROLMENT_AVAILABLE_ASSIGNMENT_REL

        join = '''
            LEFT JOIN {table} AS rel
                ON rel.assignment_id = tta."id"
                AND rel.enrolment_id = tae."id"
        '''.format(table=self._table)

        where = 'WHERE rel."id" IS NULL'

        if assignments:
            assignments = self._read_ids(assignments)
            where += f' AND tta."id" IN ({assignments})'

        if enrolments:
            enrolments = self._read_ids(enrolments)
            where += f' AND tae."id" IN ({enrolments})'

        return pattern.format(join=join, where=where)

    @api.model
    def generate_missing_records(self, assignments=None, enrolments=None):
        """
        Identifies and creates missing records for specified assignments and
        enrolments that do not currently exist in the database. The missing
        records are identified using SQL queries to perform the necessary
        checks efficiently, but the actual record creation is handled via
        Odoo's ORM to utilize business logic defined in the models and ensure
        data integrity.

        Args:
            assignments (list, optional): List of assignment IDs for which
                                          missing records need to be created.
            enrolments (list, optional): List of enrolment IDs for which
                                         missing records need to be created.

        This method constructs and executes a LEFT JOIN SQL query to identify
        gaps in the records. It then iteratively creates records using ORM
        methods, keeping track of errors and halting if the error count exceeds
        the allowed threshold.
        """
        sql = self._build_missing_records_sql(assignments, enrolments)
        results = self._execute_query(
            sql, selection=True, action='generate_missing_records'
        )
        errors = 0
        allowed = self._get_max_allowed_errors()
        for values in results:
            record = self._try_to_create_new(values)
            errors += int(len(record) == 0)
            if self._error_limit_exceeded(errors, allowed, log_method='error'):
                break

    def _old_fast_update_attempt_data(self):
        """
        Updates attempt-related data for each individual assignment by
        executing an SQL query that computes first, last, and best attempts,
        among other data. This query handles missing information by filling in
        default values.

        If self contains records, the update is restricted to those records;
        otherwise, the update is applied to all records in the database.

        This method does not use ORM; instead, it performs updates using a
        complex SQL query.
        """

        sql_pattern = '''
        WITH targets AS (
            -- This CTE is used only to limit the records to be considered

            SELECT
                "id" AS individual_id,
                assignment_id,
                enrolment_id
            FROM
                academy_tests_test_training_assignment_enrolment_rel AS rel
            WHERE TRUE {restriction}

        ), attempt_info AS (
            -- Obtains the first, last, and best attempt for each
            -- individual assignment. It does not take into account those
            -- that are still open

            SELECT DISTINCT ON ( att.individual_id )
                att.individual_id,
                FIRST_VALUE ( "id" ) OVER first_wnd AS first_attempt_id,
                FIRST_VALUE ( "id" ) OVER last_wnd AS last_attempt_id,
                FIRST_VALUE ( "id" ) OVER best_wnd AS best_attempt_id
            FROM
                academy_tests_attempt AS att
            INNER JOIN targets AS tgs
                ON tgs.individual_id = att.individual_id
            WHERE
                active
                AND closed
            WINDOW
                first_wnd AS (
                    PARTITION BY att.individual_id
                    ORDER BY "start" ASC, create_date ASC
                ),
                last_wnd AS (
                    PARTITION BY att.individual_id
                    ORDER BY "start" DESC, create_date DESC
                ),
                best_wnd AS (
                    PARTITION BY att.individual_id
                    ORDER BY final_points DESC, create_date ASC
                )
            ORDER BY
                att.individual_id
        ), attempt_count AS (
            -- Counts attempts for each individual assignment. It takes
            -- into account those that are still open.

            SELECT
                att.individual_id,
                COUNT("id")::INTEGER AS attempt_count,
                MAX ( final_points ) :: FLOAT AS max_final_points,
                MIN ( final_points ) :: FLOAT AS min_final_points,

                AVG ( final_points ) :: FLOAT AS avg_final_points,
                AVG ( right_points ) :: FLOAT AS avg_right_points,
                AVG ( wrong_points ) :: FLOAT AS avg_wrong_points,
                AVG ( blank_points ) :: FLOAT AS avg_blank_points,

                AVG ( answered_count )::INT AS avg_answered_count,
                AVG ( right_count ) :: INT AS avg_right_count,
                AVG ( wrong_count ) :: INT AS avg_wrong_count,
                AVG ( blank_count ) :: INT AS avg_blank_count,

                SUM ( passed::INT ) :: INTEGER AS passed_count,
                SUM ( (NOT passed)::INT ) :: INTEGER AS failed_count
            FROM academy_tests_attempt AS att
            INNER JOIN targets AS tgs
                ON tgs.individual_id = att.individual_id
            WHERE
                active
            GROUP BY
                att.individual_id

        ), computed_data AS (
            -- Completes missing information, such as dates or scores, and
            -- fills records with no information with default values.

            SELECT
                tgs.individual_id,

                ass.question_count,
                ass.max_points,
                ass."release" AS date_start,
                ass.expiration AS date_stop,

                enrol."id" AS enrolment_id,
                enrol.company_id,
                enrol.student_id,

                info.first_attempt_id,
                info.last_attempt_id,
                info.best_attempt_id,
                fa."end" AS first_attempt,
                la."end" AS last_attempt,
                ba."end" AS best_attempt,

                COALESCE( fa."final_points", 0.0 )::FLOAT AS first_points,
                COALESCE( la."final_points", 0.0 )::FLOAT AS last_points,
                COALESCE( ba."final_points", 0.0 )::FLOAT AS best_points,

                COALESCE( ac.attempt_count, 0 )::INTEGER AS attempt_count,

                -- Same as la.final_points
                COALESCE(ac.max_final_points, 0.0)::FLOAT AS max_final_points,
                COALESCE(ac.min_final_points, 0.0)::FLOAT AS min_final_points,

                COALESCE(ac.avg_final_points, 0.0)::FLOAT AS avg_final_points,
                COALESCE(ac.avg_right_points, 0.0)::FLOAT AS avg_right_points,
                COALESCE(ac.avg_wrong_points, 0.0)::FLOAT AS avg_wrong_points,
                COALESCE(ac.avg_blank_points, 0.0)::FLOAT AS avg_blank_points,

                COALESCE(ac.avg_answered_count,0.0)::INT AS avg_answered_count,
                COALESCE(ac.avg_right_count, 0.0)::INT AS avg_right_count,
                COALESCE(ac.avg_wrong_count, 0.0)::INT AS avg_wrong_count,
                COALESCE(ac.avg_blank_count, 0.0)::INT AS avg_blank_count,

                COALESCE(ac.passed_count, 0)::INTEGER AS passed_count,
                COALESCE(ac.failed_count, 0)::INTEGER AS failed_count
            FROM targets AS tgs
            INNER JOIN academy_tests_test_training_assignment AS ass
                ON ass."id" = tgs.assignment_id
            INNER JOIN academy_training_action_enrolment AS enrol
                    ON enrol."id" = tgs.enrolment_id
            LEFT JOIN attempt_info AS info
                ON info.individual_id = tgs.individual_id
            LEFT JOIN academy_tests_attempt AS fa
                ON fa."id" = info.first_attempt_id
            LEFT JOIN academy_tests_attempt AS la
                ON la."id" = info.last_attempt_id
            LEFT JOIN academy_tests_attempt AS ba
                ON ba."id" = info.best_attempt_id
            LEFT JOIN attempt_count AS ac
                ON ac.individual_id = tgs.individual_id
        )
        UPDATE academy_tests_test_training_assignment_enrolment_rel AS rel
        SET
            question_count = cd.question_count,
            max_points = cd.max_points,
            date_start = cd.date_start,
            date_stop = cd.date_stop,
            enrolment_id = cd.enrolment_id,
            company_id = cd.company_id,
            student_id = cd.student_id,
            first_attempt_id = cd.first_attempt_id,
            last_attempt_id = cd.last_attempt_id,
            best_attempt_id = cd.best_attempt_id,
            first_attempt = cd.first_attempt,
            last_attempt = cd.last_attempt,
            best_attempt = cd.best_attempt,
            first_points = cd.first_points,
            last_points = cd.last_points,
            best_points = cd.best_points,
            attempt_count = cd.attempt_count,
            max_final_points = cd.max_final_points,
            min_final_points = cd.min_final_points,
            avg_final_points = cd.avg_final_points,
            avg_right_points = cd.avg_right_points,
            avg_wrong_points = cd.avg_wrong_points,
            avg_blank_points = cd.avg_blank_points,
            avg_answered_count = cd.avg_answered_count,
            avg_right_count = cd.avg_right_count,
            avg_wrong_count = cd.avg_wrong_count,
            avg_blank_count = cd.avg_blank_count,
            passed_count = cd.passed_count,
            failed_count = cd.failed_count
        FROM
            computed_data AS cd
        WHERE
            cd.individual_id = rel."id";
        '''

        try:
            self.check_access_rights('write')
        except AccessError:
            message = _('You do not have the necessary permissions to update '
                        'this data.')
            raise UserError(message)

        if self:
            ids_str = ', '.join([str(record.id) for record in self])
            restriction = f' AND rel."id" IN ({ids_str}) '
        else:
            restriction = ''

        sql = sql_pattern.format(restriction=restriction)
        self._execute_query(sql, notify=True, action='update_attempt_data')

    @api.model
    def reconcile_records(self, assignments=None, enrolments=None):
        # Not neadeed: self.purge_obsolete_records(assignments, enrolments)
        self.generate_missing_records(assignments, enrolments)

        record_obj = self.env[self._name].sudo()

        domains = []

        if assignments:
            assig_domain = make_domain('assignment_id', assignments, False)
            domains.append(assig_domain)

        if enrolments:
            enrol_domain = make_domain('enrolment_id', enrolments, False)
            domains.append(enrol_domain)

        domain = AND(domains) if domains else TRUE_DOMAIN

        record_set = record_obj.search(domain)
        record_set.fast_update_attempt_data()

    @api.model
    def _get_default_attempt_data(self):
        return {
            'question_count': 0,
            'max_points': 0.0,
            'date_start': None,
            'date_stop': None,
            'enrolment_id': None,
            'company_id': None,
            'student_id': None,
            'first_attempt_id': None,
            'last_attempt_id': None,
            'best_attempt_id': None,
            'first_attempt': None,
            'last_attempt': None,
            'best_attempt': None,
            'first_points': 0.0,
            'last_points': 0.0,
            'best_points': 0.0,
            'attempt_count': 0,
            'max_final_points': 0.0,
            'min_final_points': 0.0,
            'avg_final_points': 0.0,
            'avg_right_points': 0.0,
            'avg_wrong_points': 0.0,
            'avg_blank_points': 0.0,
            'avg_answered_count': 0,
            'avg_right_count': 0,
            'avg_wrong_count': 0,
            'avg_blank_count': 0,
            'passed_count': 0,
            'failed_count': 0,
        }

    def _compute_attempt_data(self):
        values = self._get_default_attempt_data()

        assignment = self.assignment_id
        enrolment = self.enrolment_id

        date_start = datetime.combine(enrolment.register, time.min)
        date_stop = enrolment.deregister or datetime(9999, 12, 30)
        date_stop = date_stop + timedelta(days=1)
        date_stop = datetime.combine(date_stop, time.min)

        values['question_count'] = assignment.question_count
        values['max_points'] = assignment.max_points
        values['date_start'] = max(assignment.release, date_start)
        values['date_stop'] = min(assignment.expiration, date_stop)
        values['enrolment_id'] = enrolment.id
        values['company_id'] = enrolment.company_id.id
        values['student_id'] = enrolment.student_id.id

        if self.attempt_ids:
            attempt_count = len(self.attempt_ids)
            values['attempt_count'] = attempt_count

            first_attempt = self.attempt_ids.sorted(
                key=lambda r: r.start, reverse=False)[0]
            values['first_attempt_id'] = first_attempt.id
            values['first_attempt'] = first_attempt.end
            values['first_points'] = first_attempt.final_points

            last_attempt = self.attempt_ids.sorted(
                key=lambda r: r.start, reverse=True)[0]
            values['last_attempt_id'] = last_attempt.id
            values['last_attempt'] = last_attempt.end
            values['last_points'] = last_attempt.final_points

            best_attempt = self.attempt_ids.sorted(
                key=lambda r: r.final_points, reverse=True)[0]
            values['best_attempt_id'] = best_attempt.id
            values['best_attempt'] = best_attempt.end
            values['best_points'] = best_attempt.final_points

            final_points_list = self.mapped('attempt_ids.final_points')
            values['max_final_points'] = max(final_points_list)
            values['min_final_points'] = min(final_points_list)
            values['avg_final_points'] = \
                self._safe_division(sum(final_points_list), attempt_count, 0.0)

            right_points_list = self.mapped('attempt_ids.right_points')
            wrong_points_list = self.mapped('attempt_ids.wrong_points')
            blank_points_list = self.mapped('attempt_ids.blank_points')
            values['avg_right_points'] = \
                self._safe_division(sum(right_points_list), attempt_count, 0.0)
            values['avg_wrong_points'] = \
                self._safe_division(sum(wrong_points_list), attempt_count, 0.0)
            values['avg_blank_points'] = \
                self._safe_division(sum(blank_points_list), attempt_count, 0.0)

            right_count_list = self.mapped('attempt_ids.right_count')
            wrong_count_list = self.mapped('attempt_ids.wrong_count')
            blank_count_list = self.mapped('attempt_ids.blank_count')
            values['avg_right_count'] = \
                self._safe_division(sum(right_count_list), attempt_count, 0)
            values['avg_wrong_count'] = \
                self._safe_division(sum(wrong_count_list), attempt_count, 0)
            values['avg_blank_count'] = \
                self._safe_division(sum(blank_count_list), attempt_count, 0)

            answered_count_list = self.mapped('attempt_ids.answered_count')
            values['avg_answered_count'] = \
                self._safe_division(sum(answered_count_list), attempt_count, 0)

            passed_count = len(self.attempt_ids.filtered(lambda r: r.passed))
            values['passed_count'] = passed_count
            values['failed_count'] = attempt_count - attempt_count

        return values

    def fast_update_attempt_data(self):
        for record in self:
            values = record._compute_attempt_data()
            record.write(values)

    @staticmethod
    def _safe_division(dividend, divisor, default=0.0):
        try:
            result = dividend / divisor
            result = type(default)(result)
        except ZeroDivisionError:
            message = (f'Warning: Division by zero. '
                       f'Returning {default} as the result.')
            _logger.warning(message)
            result = default
        except (ValueError, TypeError) as e:
            message = (f'Warning: Invalid input {e}. '
                       f'Returning {default} as the result.')
            _logger.warning(message)
            result = default

        return result

    # -------------------------------------------------------------------------
    # Actions and Events
    # -------------------------------------------------------------------------

    def view_attempts(self):
        self.ensure_one()

        action_xid = 'academy_tests.action_test_attempts_act_window'
        act_wnd = self.env.ref(action_xid)

        name = _('Attempts')

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({
            'default_individual_id': self.id,
            'search_default_best_attempts': 0
        })

        domain = [('individual_id', '=', self.id)]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': act_wnd.res_model,
            'target': 'current',
            'name': name,
            'view_mode': act_wnd.view_mode,
            'domain': domain,
            'context': context,
            'search_view_id': act_wnd.search_view_id.id,
            'help': act_wnd.help
        }

        return serialized
