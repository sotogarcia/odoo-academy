# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Random Wizard Line

This module contains the academy.tests.random.line. an unique Odoo model
which contains all Academy Tests Random Wizard Line  attributes and behavior.

"""


from logging import getLogger
from datetime import datetime
import psycopg2.extensions
from sys import maxsize, exit

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv import expression

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


WIZARD_LINE_STATES = [
    ('step1', 'General'),
    ('step2', 'Topics/Categories'),
    ('step3', 'Tests'),
    ('step4', 'Questions'),
    ('step5', 'Restrictions')
]

# in question, in this line, exclude/include
FIELD_MAPPING = [
    ('type_id', 'type_ids', 'exclude_types'),
    ('id', 'test_ids.question_ids', 'exclude_tests'),
    ('topic_id', 'topic_ids', 'exclude_topics'),
    ('category_ids', 'category_ids', 'exclude_categories'),
    ('tag_ids', 'tag_ids', 'exclude_tags'),
    ('level_id', 'level_ids', 'exclude_levels'),
    ('id', 'question_ids', 'exclude_questions'),
]

SQL_AGREGATE_FOR_NONE = '1'
SQL_AGREGATE_FOR_ANSWERED = '1'
SQL_AGREGATE_FOR_MISTAKEN = '(SUM ( (NOT(COALESCE ( is_correct, TRUE ))::BOOLEAN) :: INTEGER ) :: NUMERIC / COUNT ( * ))'
SQL_AGREGATE_FOR_BLANK = '(SUM ( ( user_action = \'blank\' ) :: INTEGER ) :: NUMERIC / COUNT ( * ))'
SQL_AGREGATE_FOR_DOUBT = '(SUM ( ( user_action = \'doubt\' ) :: INTEGER ) :: NUMERIC / COUNT ( * ))'
SQL_AGREGATE_FOR_DOUBT_BLANK = '(SUM ( ( user_action IN ( \'doubt\', \'blank\' ) ) :: INTEGER ) :: NUMERIC / COUNT ( * ))'
SQL_AGREGATE_FOR_MISTAKEN_BLANK = '(SUM ( ((NOT(COALESCE ( is_correct, TRUE ))::BOOLEAN) OR ( user_action = \'blank\' ))::INTEGER ) :: NUMERIC / COUNT ( * ))'
SQL_AGREGATE_FOR_MISTAKEN_DOUBT = '(SUM ( ((NOT(COALESCE ( is_correct, TRUE ))::BOOLEAN) OR ( user_action = \'doubt\' ))::INTEGER ) :: NUMERIC / COUNT ( * ))'
SQL_AGREGATE_FOR_MISTAKEN_DOUBT_BLANK = '(SUM ( ((NOT(COALESCE ( is_correct, TRUE ))::BOOLEAN) OR ( user_action IN ( \'doubt\', \'blank\' ) ))::INTEGER ) :: NUMERIC / COUNT ( * ))'

SQL_BASE_FOR_COMPLEX_QUERY = '''
    SELECT
        {field}
    FROM
        "academy_tests_question"
'''

SQL_JOIN_ANSWERED = '''
    INNER JOIN (
        SELECT
            question_id as answered_question_id,
            {aggregate}::NUMERIC AS ratio
        FROM
            academy_tests_attempt_attempt_answer_rel AS rel
        {student}
        GROUP BY
            question_id
    ) AS aq ON "id" = answered_question_id
'''

SQL_JOIN_STUDENT = """
    INNER JOIN academy_tests_attempt ON attempt_id = "id"
    WHERE student_id in ({ids})
"""

SQL_JOIN_CIRCUNSCRIBE = '''
    INNER JOIN (
        SELECT DISTINCT
            question_id AS available_question_id
        FROM
            {table} AS rel1
        INNER JOIN academy_tests_test_question_rel AS rel2
            ON rel1.test_id = rel2.test_id
        WHERE {field} in ({ids})
    ) as cq
    ON "id" = available_question_id
'''

# pylint: disable=locally-disabled, R0903, W0212
class AcademyTestsRandomWizardLine(models.Model):
    """ This model is the representation of the academy tests random line

    Fields:
      name (Char)       : Human readable name which will identify each record
      description (Text): Something about the record or other information which
      has not an specific defined field to store it.
      active (Boolean)  : Checked do the record will be found by search and
      browse model methods, unchecked hides the record.

    """


    _name = 'academy.tests.random.line'
    _description = u'Academy tests, random line'


    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'

    _debug=True

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_name(),
        help="Name for this line",
        size=255,
        translate=True,
        track_visibility='onchange'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this line',
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

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help=('Place of this line in the order of the lines from parent')
    )

    state = fields.Selection(
        string='State',
        required=True,
        readonly=False,
        index=False,
        default='step1',
        help=False,
        selection=WIZARD_LINE_STATES
    )

    random_template_id = fields.Many2one(
        string='Template',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=False,
        index=False,
        default=20,
        help='Maximum number of questions can be appended'
    )

    type_ids = fields.Many2many(
        string='Types',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question.type',
        relation='academy_tests_random_line_question_type_rel',
        column1='random_line_id',
        column2='type_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_types = fields.Boolean(
        string='Exclude selected types',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    disallow_attachments = fields.Boolean(
        string='Disallow all attachments',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to exclude all questions have attachments'
    )

    test_ids = fields.Many2many(
        string='Tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed tests or leave empty to allow all',
        comodel_name='academy.tests.test',
        relation='academy_tests_random_line_test_rel',
        column1='random_line_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_tests = fields.Boolean(
        string='Exclude selected tests',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    topic_ids = fields.Many2many(
        string='Topics',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed topics or leave empty to allow all',
        comodel_name='academy.tests.topic',
        relation='academy_tests_random_line_topic_rel',
        column1='random_line_id',
        column2='topic_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_topics = fields.Boolean(
        string='Exclude selected topics',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    category_ids = fields.Many2many(
        string='Categories',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed categories or leave empty to allow all',
        comodel_name='academy.tests.category',
        relation='academy_tests_random_line_category_rel',
        column1='random_line_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_categories = fields.Boolean(
        string='Exclude selected categories',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it this to disallow selected records instead allow them'
    )

    tag_ids = fields.Many2many(
        string='Labels',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed tags or leave empty to allow all',
        comodel_name='academy.tests.tag',
        relation='academy_tests_random_line_tag_rel',
        column1='random_line_id',
        column2='tag_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_tags = fields.Boolean(
        string='Exclude selected tags',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    level_ids = fields.Many2many(
        string='Levels',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed levels or leave empty to allow all',
        comodel_name='academy.tests.level',
        relation='academy_tests_random_line_level_rel',
        column1='random_line_id',
        column2='level_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_levels = fields.Boolean(
        string='Exclude selected levels',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed questions or leave empty to allow all',
        comodel_name='academy.tests.question',
        relation='academy_tests_random_line_question_rel',
        column1='random_line_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_questions = fields.Boolean(
        string='Exclude selected questions',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it this to disallow selected records instead allow them'
    )


    # ----------- SETUP REQUERIMENTS ------------

    stock_by = fields.Selection(
        string='Stock by',
        required=True,
        readonly=False,
        index=False,
        default='not',
        help='Choose how minimum question stock will be computed',
        selection=[
            ('not', 'No restrict'),
            ('pct', 'Percent')
        ]
    )

    stock = fields.Float(
        string='Stock',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        digits=(16, 2),
        help='Minimum number of questions required to make new test'
    )

    answered_by = fields.Selection(
        string='Answered by',
        required=True,
        readonly=False,
        index=False,
        default='not',
        help='Choose how minimum answered questions will be computed',
        selection=[
            ('not', 'No restrict'),
            ('pct', 'Percent')
        ]
    )

    answered = fields.Float(
        string='Answered',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        help='Minimum number of answered questions required to make new test'
    )

    restrict_by = fields.Selection(
        string='Restrict',
        required=True,
        readonly=False,
        index=False,
        default='0',
        help='Choose how minimum question stock will be computed',
        selection=[
            ('0', 'No restrict'),
            ('1', 'Answered'),
            ('3', 'Mistaken'),
            ('5', 'Blank'),
            ('9', 'Doubt'),
            ('7', 'Mistaken/Blank'),
            ('11', 'Mistaken/Doubt'),
            ('13', 'Blank/Doubt'),
            ('15', 'Mistaken/Blank/Doubt')
        ]
    )

    supply = fields.Float(
        string='Supply',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        help='Minimum number of  mistakes/doubts/blanks required to make new test'
    )

    ratio = fields.Float(
        string='Ratio',
        required=True,
        readonly=False,
        index=False,
        default=0.5,
        digits=(16, 2),
        help='Percentaje of mistakes/doubts/blanks required to use a question in test'
    )


    # ----------------------- AUXILIARY FIELD METHODS -------------------------

    def default_name(self):
        """ Computes default value for name
        """
        current_time = datetime.now()
        return fields.Datetime.context_timestamp(self, timestamp=current_time)


    # -------------------------- MANAGEMENT FIELDS ----------------------------

    type_count = fields.Integer(
        string='Nº types',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of types',
        store=False,
        compute='compute_type_count'
    )

    @api.depends('type_ids', 'exclude_types')
    def compute_type_count(self):
        """ This computes type_count field """
        for record in self:
            sign = -1 if record.exclude_types else 1
            record.type_count = len(record.type_ids) * sign

    test_count = fields.Integer(
        string='Nº tests',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of tests',
        store=False,
        compute='compute_test_count'
    )

    @api.depends('test_ids', 'exclude_tests')
    def compute_test_count(self):
        """ This computes test_count field """
        for record in self:
            sign = -1 if record.exclude_tests else 1
            record.test_count = len(record.test_ids) * sign

    topic_count = fields.Integer(
        string='Nº topics',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of topics',
        store=False,
        compute='compute_topic_count'
    )

    @api.depends('topic_ids', 'exclude_topics')
    def compute_topic_count(self):
        """ This computes topic_count field """
        for record in self:
            sign = -1 if record.exclude_topics else 1
            record.topic_count = len(record.topic_ids) * sign

    category_count = fields.Integer(
        string='Nº categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of categories',
        store=False,
        compute='compute_category_count'
    )

    @api.depends('category_ids', 'exclude_categories')
    def compute_category_count(self):
        """ This computes category_count field """
        for record in self:
            sign = -1 if record.exclude_categories else 1
            record.category_count = len(record.category_ids) * sign

    tag_count = fields.Integer(
        string='Nº tags',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of tags',
        store=False,
        compute='compute_tag_count'
    )

    @api.depends('tag_ids', 'exclude_tags')
    def compute_tag_count(self):
        """ This computes tag_count field """
        for record in self:
            sign = -1 if record.exclude_tags else 1
            record.tag_count = len(record.tag_ids) * sign

    level_count = fields.Integer(
        string='Nº levels',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of levels',
        store=False,
        compute='compute_level_count'
    )

    @api.depends('level_ids', 'exclude_levels')
    def compute_level_count(self):
        """ This computes level_count field """
        for record in self:
            sign = -1 if record.exclude_levels else 1
            record.level_count = len(record.level_ids) * sign

    question_count = fields.Integer(
        string='Nº questions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of questions',
        store=False,
        compute='compute_question_count'
    )

    @api.depends('question_ids', 'exclude_questions')
    def compute_question_count(self):
        """ This computes question_count field """
        for record in self:
            sign = -1 if record.exclude_questions else 1
            record.question_count = len(record.question_ids) * sign


    # --------------------------- PRIVATE METHODS -----------------------------

    def _reload_on_step1(self):
        """ Builds an action which loads again transient model record using
        'step3' as state
        @note: actually this method is not used
        """
        self.write({'state': 'step1'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.tests.random.line',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new'
        }


    @staticmethod
    def _domain_item(leaf, ids, exclude):
        """ Builds a domain leaf. All leafs created by this method will be
        `in` or `not in`.

        @param leaf (string): realational field name
        @param ids (list): list of ids to include or exclude
        @param exclude (bool): True to use `not in` or False to use `in`
        """

        if ids:
            operator = 'not in' if exclude else 'in'
            return (leaf, operator, ids)

        return None


    def _get_ids(self, field_path):
        """This gets ids from given relational field set, this can be
        referred by a single field name or by dots separated field path.

        @param field_path (string): field names separated by dots, like:
        test_ids.question_ids
        @return (list): list of ids in set
        """
        result = self

        for step in field_path.split('.'):
            result = result.mapped(step)

        return result.mapped('id')


    # --------------------- COMPUTE RESTICTIONS ------------------------
    # Some restrictions can be setup for line, others will be read from
    # context (resource, active_ids, active students). Perform query to
    # get ID's with restrictions a NON ORM SQL query is needed, methods
    # in this section reads rectrictions from lina and context and to
    # build and execute this NON ORM query
    # ------------------------------------------------------------------

    @staticmethod
    def _sql_base_for_complex_query(count=False):
        """ Build the common SQL part for use in complex searches

        @param count (bool): if it's set to True the search result will
        be the number of records
        @return (tuple) SQL query string
        """

        field = 'COUNT("id")' if count else '"id" AS question_id'

        return SQL_BASE_FOR_COMPLEX_QUERY.format(field=field)


    @staticmethod
    def _sql_restriction_join(restriction, student_ids=None):
        """ Create the join SQL part to apply constraints, including
        which retrieve the answered questions

        @param restriction (int): valid restriction identifier
        @return (string) SQL query join clausule
        """

        agregate = False

        if restriction == 0:
            agregate  = SQL_AGREGATE_FOR_NONE
        elif restriction == 1:
            agregate = SQL_AGREGATE_FOR_ANSWERED
        elif restriction == 3:  # 'Mistaken'
            agregate = SQL_AGREGATE_FOR_MISTAKEN
        elif restriction == 5:  # 'Blank'
            agregate = SQL_AGREGATE_FOR_BLANK
        elif restriction == 9:  # 'Doubt'
            agregate = SQL_AGREGATE_FOR_DOUBT
        elif restriction == 7:  # 'Mistaken/Blank'
            agregate = SQL_AGREGATE_FOR_DOUBT_BLANK
        elif restriction == 11:  # 'Mistaken/Doubt'
            agregate = SQL_AGREGATE_FOR_MISTAKEN_BLANK
        elif restriction == 13:  # 'Blank/Doubt'
            agregate = SQL_AGREGATE_FOR_MISTAKEN_DOUBT
        elif restriction == 15:  # 'Mistaken/Blank/Doubt
            agregate = SQL_AGREGATE_FOR_MISTAKEN_DOUBT_BLANK
        else:
            msg = _('Usupported restriction {}').format(restriction)
            assert agregate, msg

        if restriction > 1 and student_ids:
            in_str = ', '.join([str(item) for item in student_ids])
            join_student = SQL_JOIN_STUDENT.format(ids=in_str)
        else:
            join_student = ''

        return SQL_JOIN_ANSWERED.format(
            aggregate=agregate, student=join_student)


    @staticmethod
    def _sql_circunscribe_join(res_to, res_ids):
        """ Create the join SQL ppart to restrict the results to the
        questions related to a given action or module

        @param res_to (string): this can be `module` or `action`
        @param res_ids (int): valid module or action ID

        @return (string) SQL query join clausule
        """
        assert res_to in ['action', 'module'], _('Unexpected keyword')

        table = 'academy_tests_test_available_in_training_{}_rel'
        field = 'training_{}_id'

        in_str = ', '.join([str(item) for item in res_ids])

        return SQL_JOIN_CIRCUNSCRIBE.format(
            table=table.format(res_to),
            field=field.format(res_to),
            ids=in_str
        )


    @api.model
    def _encoded_sql_query(self, query, where_params):
        """ Encode result of psycopg2.mogrify to the current cursor
        encoding after fill it with given where params

        @see https://www.compose.com/articles/formatted-sql-in-python-with-psycopgs-mogrify/

        @return (string) filled and encoded SQL query string
        """

        cr = self.env.cr

        encoding = psycopg2.extensions.encodings[cr.connection.encoding]
        sql_query = self.env.cr.mogrify(query, where_params)

        return sql_query.decode(encoding, 'replace')


    @api.model
    def _sql_where(self, domain, ratio=None):
        """ Transform a given valid Odoo domain in a valid SQL WHERE
        clausule and appends it IN THE END of the given query

        @param domain (list): Odoo valid domain
        @param ratio (float): ratio will be used in restriction

        @note ratio should be from self.ratio field, but it's optional
        in this method to allow use this in non restricion queries

        @return (string): given query with where clausule attached
        """

        where_params = None
        where_str = ''

        domain = domain or []

        qobj = self.env['academy.tests.question']

        # FROM ODOO CODE:BEGIN -> See _search method in models.py
        qobj._flush_search(domain, order=None)
        query = qobj._where_calc(domain)
        qobj._apply_ir_rules(query, 'read')

        from_clause, where_clause, where_params = query.get_sql()
        where_params = where_params or None
        # FROM ODOO CODE:END

        if(where_clause):
            where_str = " WHERE {}".format(where_clause)

        if(ratio):
            if(where_str):
                where_str += ' AND ratio >= {}'.format(ratio)
            else:
                where_str = " WHERE ratio >= {}".format(ratio)

        if where_str:
            where_str = self._encoded_sql_query(where_str, where_params)

        return where_str


    @staticmethod
    def _unpack(arguments):
        """ This will be used in _complex_search method to unpack
        arguments. If the argument does not exist it will be set to its
        default value.

        @param arguments (dict): dictionary with arguments
        @return (tuple) arguments in order
        """
        arguments = arguments or {}

        domain = arguments.get('domain', [])
        restrict = arguments.get('restriction', 0)
        ratio =  arguments.get('ratio', 0)
        resource = arguments.get('resource', None)
        res_ids = arguments.get('res_ids', [-1])
        student_ids = arguments.get('student_ids', None)

        return domain, restrict, ratio, resource, res_ids, student_ids


    @api.model
    def _complex_search(self, args, limit=None, count=False):
        """ Performs a complex search with for given line restriction

        @param args (dict): dictionary which can contains domain,
        restriction, ratio, resource and res_ids
        @param limit (int): limit of records
        @param count (bool): if it's set to True the search result will
        be the number of records

        @return (list or int) if count has been set to False then
        returned value will be a list of question ID's, otherwise the
        result will be the number of records
        """
        domain, restriction, ratio, resource, res_ids, student_ids = \
            self._unpack(args)
        query = self._sql_base_for_complex_query(count)

        if restriction > 0:
            query +=  self._sql_restriction_join(
                restriction, student_ids)

        if resource in ['action', 'module'] and res_ids:
            query +=  self._sql_circunscribe_join(resource, res_ids)

        if restriction > 1:
            query += self._sql_where(domain, ratio)
        else:
            query += self._sql_where(domain, None)

        if (limit or limit == 0) and not count:
            query += ' limit {}'.format(limit)

        result = self._execute_complex_query(query)

        if(count):
            result = result[0][0] if result and result[0] else 0
        else:
            result = [item[0] for item in (result or[])]

        return result


    @api.model
    def _execute_complex_query(self, query):
        """ Use cursor to execute raw given query and fetch result. In
        addition, this method can send query string to global logger.

        @param query (string): valid raw SQL query string
        @return (list) recordset values [(value,), ...] where value can
        be a question_id or count result
        """

        if self.env.cr.sql_log or self._debug:
            query_str = query.replace("\n", " ")
            _logger.debug("complex_query: %s", query_str)

        self.env.cr.execute(query)

        return self.env.cr.fetchall()


    def _quantity_for(self, percent_field):
        """ Computes the percentage over the quantity and rounds result
        to an integer

        @return (int) percentage over the quantity
        """

        self.ensure_one()

        percent = getattr(self, percent_field, 0)

        return int(round(percent * self.quantity))


    def _get_restriction(self):
        """ Get current line restrict_by field value (as text) and cast
        it to an integer
        @return (int) restriction ID as an integer
        """

        self.ensure_one()
        return int(self.restrict_by)


    @staticmethod
    def _with(in_dict, update=None):
        """ Returns an updated copy for given dictionary
        @param update (dict): key,value pairs to update
        @return (dict): a new updated dictionary
        """
        new_dict = in_dict.copy()

        if update:
            for key, value in update.items():
                new_dict[key] = value

        return new_dict


    def _great_or_equal(self, expected, result, complement=''):
        """ Assert result is greater or equal to result and raises
        an exception with a message that has self name and complement
        """

        msg = _('There are not enough {} questions for the line {}')
        assert result >= expected, msg.format('available', self.name)


    def _from_context(self):
        """ Gets the active model name, and related ID's from context,
        it also gets student ID if it has been passed in context

        @return (tuple) model name and a list with active ids. If there
        is no model or active ids then return None, None
        """

        context = self.env.context

        model = context.get('active_model', None)
        active_ids = context.get('active_ids', None)
        student_ids = context.get('student_ids', None)

        if not model or not active_ids:
            model, active_ids = None, None

        if isinstance(active_ids, int):
            active_ids = [active_ids]

        return model, active_ids, student_ids


    def _from_enrolment(self, enrolment_ids):
        """ Check if given enrolment ID's has only one element and, if
        it is true, it gets resource, ID's and student related with the
        enrolment. The obtained resource will be 'action' if enrolment
        has no modules, otherwilse resource will be 'module'.

        @return (tuple) If given enrolment_ids is a single element list
        result will be related resource, ID's and student ID, otherwise
        result will be None, None, None
        """

        resource, ids, student_ids = None, None, None

        if enrolment_ids and len(enrolment_ids) == 1:
            enrol_obj = self.env['academy.training.action.enrolment']
            enrol_set = enrol_obj.browse(enrolment_ids)

            if(enrol_set):
                if (enrol_set.training_module_ids):
                    resource = 'module'
                    ids = enrol_set.training_module_ids.mapped('id')
                else:
                    resource = 'action'
                    ids = enrol_set.training_action_id.id

                student_ids = [enrol_set.student_id.id]

        return resource, ids, student_ids


    def _get_from_context(self):
        """ Get circunscription from context
        """
        models = ['academy.training.action', 'academy.training.module']

        model, active_ids, student_ids = self._from_context()

        if model in models:
            resource = model.split('.')[2]
        elif model == 'academy.training.action.enrolment':
            resource, active_ids, student_ids = \
                self._from_enrolment(active_ids)
        else:
            resource, active_ids, student_ids = None, None, None

        return resource, active_ids, student_ids


    def _get_restriction_arguments(self, domain=None):
        """ Retrieve needed arguments to perform a _complex_search.
        These arguments come from:
          - line record (ratio, restriction)
          - context (resource, res_ids, student_ids)
          - given as argument (domain)

        @param domain (list): valid Odoo domain
        @return (dict) dictionary with all arguments
        """

        self.ensure_one()

        resource, res_ids, student_ids = self._get_from_context()

        return dict(
            domain=domain,
            restriction=self._get_restriction(),
            ratio=self.ratio,
            resource=resource,
            res_ids=res_ids,
            student_ids=student_ids
        )


    def _assert_restriction(self, in_args, found_before=0):
        """ Assert restriction if has been set and raises
        an exception with a message that has self name and complement
        if assertion is false

        @param in_args (dict): dictionary which can contains domain,
        restriction, ratio, resource and res_ids
        @param found_before (int): Number of currently known questions
        matching the restriction

        @return (int) number of found records matching the restriction
        """

        result = 0
        expected = self._quantity_for('supply')
        restriction = self._get_restriction()

        if(restriction > 1 and expected > found_before):
            args = self._with(in_args, dict(restriction=restriction))
            result = self._complex_search(args, count=True)
            self._great_or_equal(expected, result, 'matching')

        return result


    def _assert_answered(self, in_args, found_before=0):
        """ Assert exists a minimum number of answered questions if
        this value has been set and raises an exception with a message
        that has self name and complement if assertion is false

        @param in_args (dict): dictionary which can contains domain,
        restriction, ratio, resource and res_ids
        @param found_before (int): Number of currently known questions
        matching the restriction

        @return (int) number of found records matching the restriction
        """

        result = 0
        expected = self._quantity_for('answered')

        if(self.answered_by != 'not' and expected > found_before):
            aargs = self._with(in_args, dict(restriction=1))
            result = self._complex_search(args, count=True)
            self._great_or_equal(expected, result, 'answered')

        return result


    def _assert_stock(self, in_args, found_before=0):
        """ Assert exists a minimum number of questions if this value
        has been set and raises an exception with a message that has
        self name and complement if assertion is false

        @param in_args (dict): dictionary which can contains domain,
        restriction, ratio, resource and res_ids
        @param found_before (int): Number of currently known questions
        matching the restriction

        @return (int) number of found records matching the restriction
        """

        result = 0
        expected = self._quantity_for('stock')

        if(self.stock_by != 'not' and expected > found_before):
            args = self._with(in_args, dict(restriction=0))
            result = question_set.search(args, count=True)
            self._great_or_equal(expected, result, 'available')

        return result


    # --------------------------- PUBLIC METHODS ------------------------------

    def get_leafs(self):
        """ Walk over field mapping making domain leafs for each of those that
         have been set.

        @note: FIELD_MAPPING has been defined at the top of this module, it's
        a list of items like: ('type_id', 'type_ids', 'exclude_types')

        @return (list): list of domain leafs without ampersand
        """

        self.ensure_one()

        leafs = []
        for field_map in FIELD_MAPPING:
            leaf = field_map[0]
            ids = self._get_ids(field_map[1])
            exclude = getattr(self, field_map[2])
            ditem = self._domain_item(leaf, ids, exclude)
            if ditem:
                leafs.append(ditem)

        if self.disallow_attachments:
            leafs.append(('ir_attachment_ids', '=', False))

        return leafs


    def get_domain(self, extra_leafs=None):
        """ Search for questions to append
        """

        self.ensure_one()

        domain = self.get_leafs()
        if extra_leafs:
            domain = domain + extra_leafs

        if len(domain) > 1:
            domain = ['&'] + domain

        msg = _('Domain {} will be used to append random questions')
        _logger.info(msg.format(domain))

        return domain


    def perform_search(self, extra_leafs=None):
        """ Reads values from each line in recordset, performs search and
        returns question ids

        @param extra_leafs: list with extra leafs to be append to domain
        """

        # STEP1: Create an empty question recordset with random sort context
        ctx = {'sort_by_random': True}
        question_set = self.env['academy.tests.question'].with_context(ctx)

        # STEP2: Ensure extra_leafs is a list
        extra_leafs = extra_leafs or []

        for record in self:

            # STEP3: Merge extra_leafs with a new leaf witch excludes current
            # accumulate questions
            exclusion_leafs = extra_leafs
            if question_set:
                qids = question_set.mapped('question_id')
                exclusion_leafs.append(('id', 'not in', qids))

            # STEP 4: Build domain with line values and merge exclusion leafs
            domain = record.get_domain(exclusion_leafs)

            # STEP 5: Check restrictions, minimum answered and stock
            args = record._get_restriction_arguments(domain)
            found1 = record._assert_restriction(args, 0)
            found2 = record._assert_answered(args, max(0, found1))
            record._assert_stock(args, max(0, found1, found2))

            # STEP 6: Perform the restricted search and overwrite line
            # domain using the obtained IDs
            if(args['restriction'] > 0):
                ids = record._complex_search(args, limit=record.quantity)
                domain = [('id', 'in', ids)]

            # STEP 7: Perform search and append to previouly created recordset
            limit = record.quantity
            question_set += question_set.search(domain, limit=limit)

        return question_set
