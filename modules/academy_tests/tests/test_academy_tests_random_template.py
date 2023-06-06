# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.tests.common import TransactionCase
from logging import getLogger
from odoo.osv.expression import AND

from datetime import datetime
import sys


_logger = getLogger(__name__)


class TestAcademyTestsRandomTemplate(TransactionCase):
    _template_xid = 'academy_tests.academy_tests_random_template_demo'
    _msg = 'The obtained recordset is not equal to expected recordset'

    def setUp(self):
        super(TestAcademyTestsRandomTemplate, self).setUp()

        if not self._demo_data_has_been_loaded():
            self.skipTest("Demo data has not been loaded")

        self._question_obj = self.env['academy.tests.question']
        self._template_obj = self.env['academy.tests.random.template']

        self._demo = self.env.ref(self._template_xid)
        self._domain = [
            ('depends_on_id', '=', False),
            ('status', '=', 'ready')
        ]

    @staticmethod
    def _callers_name():
        return sys._getframe(2).f_code.co_name

    def _demo_data_has_been_loaded(self):
        """ Check if academy_tests.academy_tests_random_template_demo record
        exists in database.

        Returns:
            bool -- True if record exists False otherwise
        """

        ir_model_domain = [
            ('module', '=', 'academy_tests'),
            ('model', '=', 'academy.tests.random.template'),
            ('name', '=', 'academy_tests_random_template_demo')
        ]
        ir_model_obj = self.env['ir.model.data']
        ir_model_set = ir_model_obj.search(ir_model_domain)

        return bool(ir_model_set)

    def _get_template(self, lines=0):
        """ Create a new academy.tests.random.template with the given number of
        empty lines.

        Keyword Arguments:
            lines {number} -- Number of lines to append in (default: {0})

        Returns:
            recorset -- Odoo recordset with a single random template
        """

        values = []
        for index in range(0, lines):
            values.append((0, 0, {}))

        template = self._template_obj.create({
            'name': 'Testing',
            'description': 'Testing template',
            'active': True,
            'parent_id': self._demo.id,
            'random_line_ids': values
        })

        return template

    def _assert_equal(self, set1, set2):
        """ Sort two given recordsets to compair them

        Arguments:
            set1 {recordset} -- Odoo valid recordset
            set2 {recordset} -- Odoo valid recordset
        """

        set1 = set1.sorted(lambda x: x.id),
        set2 = set2.sorted(lambda x: x.id),

        self.assertEqual(set1, set2, self._msg)

    def _one_line_with_ids(self, id_name, ids_name, ids, exname, exvalue):
        """ This searchs questions using a simple domain and than it creates
        new test using new template. Questions in new test must be the same
        as obtainted with previously used simple domain.
        """

        # STEP 1: Search using a simple domain
        operator = 'not in' if exvalue else 'in'
        domain = AND([self._domain, [(id_name, operator, ids)]])
        question_set = self._question_obj.search(domain)

        if question_set:
            template = self._get_template(lines=1)

            # STEP 2: Configure new template
            template.random_line_ids[0].quantity = len(question_set)
            setattr(template.random_line_ids[0], ids_name, [(6, 0, ids)])
            setattr(template.random_line_ids[0], exname, exvalue)

            # STEP 3: Create the new test using template
            test_set = template.new_test(gui=False)

            # STEP 4: Compare both result recordsets
            obtained_set = test_set.mapped('question_ids.question_id')
            self._assert_equal(question_set, obtained_set)

    def _one_line_with_answers(self, mina, maxa, exclude):
        """ This searchs questions using a simple domain and than it creates
        new test using new template. Questions in new test must be the same
        as obtainted with previously used simple domain.

        NOTE: This method is specific to be used with template answers section
        """

        # STEP 1: Build a simple domain
        domain = ['|'] if exclude else []
        domain.append(('answer_count', '<' if exclude else '>=', mina))
        domain.append(('answer_count', '>' if exclude else '<=', maxa))
        domain = AND([self._domain, domain])

        # STEP 2: Search using the simple domain
        question_set = self.env['academy.tests.question']
        question_set = question_set.search(domain)

        if question_set:
            template = self._get_template(lines=1)

            # STEP 3: Configure new template
            template.random_line_ids[0].quantity = len(question_set)
            template.random_line_ids[0].number_of_answers = True
            template.random_line_ids[0].minimum_answers = mina
            template.random_line_ids[0].maximum_answers = maxa
            template.random_line_ids[0].exclude_answers = exclude

            # STEP 4: Create the new test using template
            test_set = template.new_test(gui=False)

            # STEP 5: Compare both result recordsets
            obtained_set = test_set.mapped('question_ids.question_id')
            self._assert_equal(question_set, obtained_set)

    def _one_line_categorization(self, domain, operation, exclude):
        """ Perform a search using a given domain, than setup a new template
        and use it to create a new tests. The set of questions in the new test
        must be the same as it had been obtained from first search.

        Arguments:
            domain {list} -- Odoo valid domain to perform the first search
            operation {list} -- list of Many2many operations will be passed
            to categorization_ids field in template.
            exclude {bool} -- ``exclude_categorization`` field value
        """

        # STEP 1: Search using the given simple domain
        domain = AND([self._domain, domain])
        question_set = self._question_obj.search(domain)

        if question_set:
            template = self._get_template(lines=1)

            # STEP 2: Configure new template using given operation(s)
            template.random_line_ids[0].quantity = len(question_set)
            template.random_line_ids[0].categorization_ids = operation
            template.random_line_ids[0].exclude_categorization = exclude

            # STEP 3: Create the new test using template
            test_set = template.new_test(gui=False)

            # STEP 4: Compare both result recordsets
            obtained_set = test_set.mapped('question_ids.question_id')
            self._assert_equal(question_set, obtained_set)

    def _one_line_context(self, qset, cref, tests, questions, exclude):
        """ Create new test using context (test and/or questions), then
        compares obtained resultset with the given question recordset.

        Arguments:
            qset {recordset} -- Expected question recordset
            cref {recordset} -- Action or enrolment will be used as context
            tests {mixed} -- True to use test context
            questions {mixed} -- True to use question context
            exclude {bool} -- True to exclude context (tests and/or questions)
        """

        question_set = qset

        if question_set:
            template = self._get_template(lines=1)

            template.random_line_ids[0].quantity = len(question_set)
            template.training_ref = cref

            if tests is not None:
                template.random_line_ids[0].tests_by_context = tests
                template.random_line_ids[0].exclude_tests = exclude
            if questions is not None:
                template.random_line_ids[0].questions_by_context = questions
                template.random_line_ids[0].exclude_questions = exclude

            test_set = template.new_test(gui=False)

            obtained_set = test_set.mapped('question_ids.question_id')

            self._assert_equal(question_set, obtained_set)

    def _add_questions(self, number):
        ctx = {'sort_by_random': True}

        for index in range(0, number):
            qtype = self.env['academy.tests.question'].with_context(
                ctx).search([], limit=1)
            qtopic = self.env['academy.tests.topic'].with_context(
                ctx).search([], limit=1)
            qlevel = self.env['academy.tests.level'].with_context(
                ctx).search([], limit=1)
            qcategory = self.env['academy.tests.category'].with_context(
                ctx).search([('topic_id', '=', qtopic.id)], limit=1)
            qversion = self.env['academy.tests.topic.version'].with_context(
                ctx).search([('topic_id', '=', qtopic.id)], limit=1)

            values = {
                'name': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                'topic_id': qtopic.id,
                'topic_version_ids': [(4, qversion.id, 0)],
                'category_ids': [(4, qcategory.id, 0)],
                'level_id': qlevel.id,
                'type_id': qtype.id,
                'answer_ids': [
                    (0, 0, {'name': 'a'}),
                    (0, 0, {'name': 'b'}),
                    (0, 0, {'name': 'x', 'is_correct': True})
                ]
            }

            self.env['academy.tests.question'].write(values)

    def test_empty_line(self):
        """ Perform a test. A random template whithout lines must return an
        empty recordset.
        """

        template = self._get_template()
        test_set = template.new_test(gui=False)
        obtained_set = test_set.mapped('question_ids.question_id')

        self.assertEqual(self._question_obj, obtained_set, self._msg)

    def test_level(self):
        """ Perform several tests using ``level_ids`` template field.
        """

        easy = self.env.ref('academy_tests.academy_level_12')
        self._one_line_with_ids(
            'level_id', 'level_ids', [easy.id], 'exclude_levels', False)

        med = self.env.ref('academy_tests.academy_level_13')
        self._one_line_with_ids(
            'level_id', 'level_ids', [med.id], 'exclude_levels', True)

        two_ids = [med.id, easy.id]
        self._one_line_with_ids(
            'level_id', 'level_ids', two_ids, 'exclude_levels', False)

        self._one_line_with_ids(
            'level_id', 'level_ids', two_ids, 'exclude_levels', True)

    def test_type(self):
        """ Perform several tests using ``type_ids`` template field.
        """

        teo = self.env.ref('academy_tests.academy_tests_question_type_1')
        self._one_line_with_ids(
            'type_id', 'type_ids', [teo.id], 'exclude_types', False)

        sup = self.env.ref('academy_tests.academy_tests_question_type_3')
        self._one_line_with_ids(
            'type_id', 'type_ids', [sup.id], 'exclude_types', True)

        two_ids = [teo.id, sup.id]
        self._one_line_with_ids(
            'type_id', 'type_ids', two_ids, 'exclude_types', False)

        self._one_line_with_ids(
            'type_id', 'type_ids', two_ids, 'exclude_types', True)

    def test_owner(self):
        """ Perform several tests using ``owner_ids`` template field.
        """

        prof = self.env.ref('academy_base.res_users_demo_teacher')
        self._one_line_with_ids(
            'owner_id', 'owner_ids', [prof.id], 'exclude_owners', False)

        tech = self.env.ref('academy_base.res_users_demo_technical')
        self._one_line_with_ids(
            'owner_id', 'owner_ids', [tech.id], 'exclude_owners', True)

        two_ids = [prof.id, tech.id]
        self._one_line_with_ids(
            'owner_id', 'owner_ids', two_ids, 'exclude_owners', False)

        self._one_line_with_ids(
            'owner_id', 'owner_ids', two_ids, 'exclude_owners', True)

    def test_answers(self):
        self._one_line_with_answers(2, 3, False)

        self._one_line_with_answers(4, 4, False)

        self._one_line_with_answers(2, 3, True)

    def test_authorship(self):
        """ Perform several tests using at the same time ``own_ids`` and
        ``authorship`` fields.
        """

        tech = self.env.ref('academy_base.res_users_demo_technical')

        for key, value in {'own': True, 'third': False}.items():

            # STEP 1: Search usign a simple domain
            domain = [
                ('authorship', '=', value),
                ('owner_id', 'in', [tech.id])
            ]
            domain = AND([self._domain, domain])
            question_set = self._question_obj.search(domain)

            if question_set:
                template = self._get_template(lines=1)

                # STEP 2: Configure the unique template line
                template.random_line_ids[0].quantity = len(question_set)
                template.random_line_ids[0].authorship = key
                template.random_line_ids[0].owner_ids = [(4, tech.id, 0)]
                test_set = template.new_test(gui=False)

                # STEP 3: Compare the obtained recordsets
                obtained_set = test_set.mapped('question_ids.question_id')
                self._assert_equal(question_set, obtained_set)

    def test_attachments(self):
        """ Perform several tests using ``ir_attachment_ids`` field
        """

        for key, value in {'with': True, 'without': False}.items():

            # STEP 1: Search usign a simple domain
            operator = '!=' if value else '='
            domain = [('ir_attachment_ids', operator, False)]
            domain = AND([self._domain, domain])
            question_set = self._question_obj.search(domain)

            if question_set:
                template = self._get_template(lines=1)

                # STEP 2: Configure the unique template line
                template.random_line_ids[0].quantity = len(question_set)
                template.random_line_ids[0].attachments = key
                test_set = template.new_test(gui=False)

                # STEP 3: Compare the obtained recordsets
                obtained_set = test_set.mapped('question_ids.question_id')
                self._assert_equal(question_set, obtained_set)

    def test_categorize(self):

        erp = 'academy_tests.academy_tests_topic_demo_1'
        thirteen = 'academy_tests.academy_tests_topic_version_demo_1'
        dev = 'academy_tests.academy_tests_tag_demo_brand'
        brand = 'academy_tests.academy_tests_category_demo_development'

        erp = self.env.ref(erp)
        thirteen = self.env.ref(thirteen)
        dev = self.env.ref(dev)
        brand = self.env.ref(brand)

        # STEP 1: Test with topic
        domain = [('topic_id', 'in', [erp.id])]
        o2m = [(0, 0, {'topic_id': erp.id})]
        self._one_line_categorization(domain, o2m, False)

        # STEP 2: Test with topic and version
        domain = [
            ('topic_id', 'in', [erp.id]),
            ('topic_version_ids', '=', [thirteen.id])
        ]
        o2m = [(0, 0, {
            'topic_id': erp.id,
            'topic_version_ids': [(4, thirteen.id, None)]
        })]
        self._one_line_categorization(domain, o2m, False)

        # STEP 3: Test with topic, version and category
        domain = [
            ('topic_id', 'in', [erp.id]),
            ('topic_version_ids', '=', [thirteen.id]),
            ('category_ids', '=', [brand.id])
        ]
        o2m = [(0, 0, {
            'topic_id': erp.id,
            'topic_version_ids': [(4, thirteen.id, None)],
            'category_ids': [(4, brand.id, None)]
        })]
        self._one_line_categorization(domain, o2m, False)

        # STEP 4: Test excluding topic
        domain = [('topic_id', 'not in', [erp.id])]
        o2m = [(0, 0, {'topic_id': erp.id})]
        self._one_line_categorization(domain, o2m, True)

        # STEP 5: Test excluding topic and version
        domain = [
            '|',
            ('topic_id', 'not in', [erp.id]),
            ('topic_version_ids', '!=', [thirteen.id])
        ]
        o2m = [(0, 0, {
            'topic_id': erp.id,
            'topic_version_ids': [(4, thirteen.id, None)]
        })]
        self._one_line_categorization(domain, o2m, True)

        # STEP 6: Test excluding topic, version and category
        domain = [
            '|',
            ('topic_id', 'not in', [erp.id]),
            '|',
            ('topic_version_ids', '!=', [thirteen.id]),
            ('category_ids', '!=', [brand.id])
        ]
        o2m = [(0, 0, {
            'topic_id': erp.id,
            'topic_version_ids': [(4, thirteen.id, None)],
            'category_ids': [(4, brand.id, None)]
        })]
        self._one_line_categorization(domain, o2m, True)

    def test_test(self):
        test_demo = self.env.ref('academy_tests.academy_tests_demo_1')
        question_set = test_demo.mapped('question_ids.question_id')

        if question_set:
            template = self._get_template(lines=1)

            template.random_line_ids[0].quantity = len(question_set)
            template.random_line_ids[0].test_ids = [(4, test_demo.id, None)]
            template.random_line_ids[0].exclude_tests = False
            test_set = template.new_test(gui=False)

            obtained_set = test_set.mapped('question_ids.question_id')

            self._assert_equal(question_set, obtained_set)

        domain = [('id', 'not in', question_set.mapped('id'))]
        question_set = question_set.search(domain)

        if question_set:
            template = self._get_template(lines=1)

            template.random_line_ids[0].quantity = len(question_set)
            template.random_line_ids[0].test_ids = [(4, test_demo.id, None)]
            template.random_line_ids[0].exclude_tests = True
            test_set = template.new_test(gui=False)

            obtained_set = test_set.mapped('question_ids.question_id')

            self._assert_equal(question_set, obtained_set)

    def test_questions(self):
        q_demo = self.env.ref('academy_tests.academy_tests_question_demo_6')

        if q_demo:
            template = self._get_template(lines=1)

            template.random_line_ids[0].quantity = len(q_demo)
            template.random_line_ids[0].question_ids = [(4, q_demo.id, None)]
            template.random_line_ids[0].exclude_questions = False
            test_set = template.new_test(gui=False)

            obtained_set = test_set.mapped('question_ids.question_id')

            self._assert_equal(q_demo, obtained_set)

        domain = [('id', '!=', q_demo.id)]
        question_set = q_demo.search(domain)

        if question_set:
            template = self._get_template(lines=1)

            template.random_line_ids[0].quantity = len(question_set)
            template.random_line_ids[0].question_ids = [(4, q_demo.id, None)]
            template.random_line_ids[0].exclude_questions = True
            test_set = template.new_test(gui=False)

            obtained_set = test_set.mapped('question_ids.question_id')

            self._assert_equal(question_set, obtained_set)

    def test_context(self):
        action = self.env.ref('academy_base.academy_training_action_demo_1')
        test_set = action.mapped('available_assignment_ids.test_id')
        question_set = test_set.mapped('question_ids.question_id')

        # STEP 1: Tests in an action
        self._one_line_context(question_set, action, True, None, False)

        # STEP 2: Tests not in an action
        self._add_questions(2)
        domain = [('id', 'not in', question_set.mapped('id'))]
        question_set = question_set.search(domain)
        self._one_line_context(question_set, action, True, None, True)

        # STEP 3: Questions in an action
        question_set = action.mapped(
            'training_activity_id.available_question_ids')
        self._one_line_context(question_set, action, None, True, False)

        # STEP 4: Questions not in an action
        self._add_questions(2)
        domain = [('id', 'not in', question_set.mapped('id'))]
        question_set = question_set.search(domain)
        self._one_line_context(question_set, action, None, True, True)

        enrolment_xid = 'academy_base.academy_training_action_enrolment_demo_1'
        enrolment = self.env.ref(enrolment_xid)
        test_set = action.mapped('available_assignment_ids.test_id')
        question_set = test_set.mapped('question_ids.question_id')

        # STEP 5: Tests in an enrolment
        self._one_line_context(question_set, enrolment, True, None, False)

        # STEP 6: Tests not in an enrolment
        self._add_questions(2)
        domain = [('id', 'not in', question_set.mapped('id'))]
        question_set = question_set.search(domain)
        self._one_line_context(question_set, enrolment, True, None, True)

        # STEP 7: Questions in an enrolment
        question_set = enrolment.mapped('available_question_ids')
        self._one_line_context(question_set, enrolment, None, True, False)

        # STEP 8: Questions not in an enrolment
        self._add_questions(2)
        domain = [('id', 'not in', question_set.mapped('id'))]
        question_set = question_set.search(domain)
        self._one_line_context(question_set, enrolment, None, True, True)

    def test_several_lines(self):
        """ Perform a search with using two lines topic, version and category,
        and the same search using a simple domain. Both results must be equal.
        """

        t1 = self.env.ref('academy_tests.academy_tests_topic_demo_1')
        t2 = self.env.ref('academy_tests.academy_tests_topic_demo_2')
        c1 = self.env.ref(
            'academy_tests.academy_tests_category_demo_development')
        c2 = self.env.ref('academy_tests.academy_tests_category_demo_concepts')
        v1 = self.env.ref('academy_tests.academy_tests_topic_version_demo_1')
        v2 = self.env.ref('academy_tests.academy_tests_topic_version_demo_2')

        domain = [
            ('topic_id', 'in', [t1.id, t2.id]),
            ('topic_version_ids', '=', [v1.id, v2.id]),
            ('category_ids', '=', [c1.id, c2.id])
        ]

        o2m = [
            (0, 0, {
                'topic_id': t1.id,
                'topic_version_ids': [(4, v1.id, None)],
                'category_ids': [(4, c1.id, None)]
            }),
            (0, 0, {
                'topic_id': t2.id,
                'topic_version_ids': [(4, v2.id, None)],
                'category_ids': [(4, c2.id, None)]
            }),
        ]

        self._one_line_categorization(domain, o2m, False)
