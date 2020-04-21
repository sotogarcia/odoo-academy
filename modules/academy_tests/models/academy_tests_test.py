# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the real life academy tests

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

TODO:

- [ ] Remove lang field and related methods
- [ ] Expiration date
- [ ] _sql_constraint that prevents duplicate questions
- [x] Allow to create questions (question_rel should have default method
to create inherited question)
- [x] Question type should be displayed in tree view
- [x] Improve topic tree view shown inside the test form

"""


from logging import getLogger
from operator import itemgetter
from random import shuffle as random_shuffle

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.addons.academy_base.models.lib.custom_model_fields import Many2manyThroughView
from odoo.tools.safe_eval import safe_eval
from .lib.libuseful import ACADEMY_TESTS_TEST_TOPIC_IDS_SQL



# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903, W0212
class AcademyTestsTest(models.Model):
    """ Stored tests which can be reused in future
    """

    _name = 'academy.tests.test'
    _description = u'Academy tests, test'

    _rec_name = 'name'
    _order = 'write_date DESC, create_date DESC'

    _inherit = ['image.mixin', 'mail.thread']


    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name for this test",
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
        help='Something about this test',
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

    preamble = fields.Text(
        string='Preamble',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='What it is said before beginning to test',
        translate=True
    )

    question_ids = fields.One2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test.question.rel',
        inverse_name='test_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        # oldname='academy_question_ids'
    )

    answers_table_ids = fields.One2many(
        string='Answers table',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Summary with answers table',
        comodel_name='academy.tests.answers.table',
        inverse_name='test_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        # oldname='academy_answers_table_ids'
    )

    random_wizard_id = fields.Many2one(
        string='Random set',
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

    owner_id = fields.Many2one(
        string='Owner',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_owner_id(),
        help='Current test owner',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        groups='academy_base.academy_group_technical'
    )


    # -------------------------- MANAGEMENT FIELDS ----------------------------

    question_count = fields.Integer(
        string='Number of questions',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Number of questions in test',
        compute='_compute_question_count'
    )

    # @api.multi
    @api.depends('question_ids')
    def _compute_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)

    topic_ids = Many2manyThroughView(
        string='Topics',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.topic',
        relation='academy_tests_test_topic_rel',
        column1='test_id',
        column2='topic_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TESTS_TEST_TOPIC_IDS_SQL
    )

    topic_count = fields.Integer(
        string='Number of topics',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Display the number of topics related with test',
        compute=lambda self: self._compute_topic_count()
    )

    # @api.multi
    @api.depends('question_ids')
    def _compute_topic_count(self):
        for record in self:
            question_set = record.question_ids.mapped('question_id')
            topic_set = question_set.mapped('topic_id')
            ids = topic_set.mapped('id')

            record.topic_count = len(ids)

    topic_id = fields.Many2one(
        string='Topic',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute=lambda self: self._compute_topic_id()
    )

    # @api.multi
    @api.depends('question_ids')
    def _compute_topic_id(self):
        for record in self:
            rel_ids = record.question_ids.filtered(
                lambda rel: rel.question_id.topic_id)
            question_ids = rel_ids.mapped('question_id')
            topics = {k.id : 0 for k in question_ids.mapped('topic_id')}

            if not topics:
                record.topic_id = None
            else:
                for question_id in question_ids:
                    _id = question_id.topic_id.id
                    topics[_id] = topics[_id] + 1

                topic_id = max(topics.items(), key=itemgetter(1))[0]

                topic_obj = self.env['academy.tests.topic']
                record.topic_id = topic_obj.browse(topic_id)


    lang = fields.Char(
        string='Language',
        required=True,
        readonly=True,
        index=False,
        help=False,
        size=50,
        translate=False,
        compute='_compute_lang',
    )

    # ----------------------- AUXILIARY FIELD METHODS -------------------------

    def _default_owner_id(self):
        uid = 1
        if 'uid' in self.env.context:
            uid = self.env.context['uid']

        return uid


    @api.depends('name')
    def _compute_lang(self):
        """ Gets the language used by the current user and sets it as `lang`
            field value
        """

        user_id = self.env['res.users'].browse(self.env.uid)

        for record in self:
            record.lang = user_id.lang


    def import_questions(self):
        """ Runs a wizard to import questions from plain text
        @note: actually this method is not used
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.tests.question.import.wizard',
            'view_mode': 'form',
            # 'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'default_test_id' : self.id}
        }


    # @api.multi
    def random_questions(self):
        """ Runs wizard to append random questions. This allows uses to set
        filter criteria, maximum number of questions, etc.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.tests.random.wizard',
            'view_mode': 'form',
            # 'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'default_test_id' : self.id}
        }


    # @api.multi
    def show_questions(self):
        """ Runs default view for academy.tests.question with a filter to
        show only current test questions
        """

        act_wnd = self.env.ref(
            'academy_tests.action_questions_keep_items_act_window')

        if act_wnd.domain:
            if isinstance(act_wnd.domain, str):
                domain = safe_eval(act_wnd.domain)
            else:
                domain = act_wnd.domain
        else:
            domain = []

        ids = self.question_ids.mapped('question_id').mapped('id')
        domain.append(('id', 'in', ids))

        values = {
            'type' : act_wnd['type'],
            'name' : act_wnd['name'],
            'res_model' : act_wnd['res_model'],
            'view_mode' : act_wnd['view_mode'],
            'target' : act_wnd['target'],
            'domain' : domain,
            'context' : self.env.context,
            'limit' : act_wnd['limit'],
            'help' : act_wnd['help'],
            'view_ids' : act_wnd['view_ids'],
            'views' : act_wnd['views']
        }

        if act_wnd.search_view_id:
            values['search_view_id'] = act_wnd['search_view_id'].id

        return values


    @api.model
    def create(self, values):
        """ Create a new record for a model AcademyTestsTest
            @param values: provides a data for new record

            @return: returns a id of new record
        """
        result = super(AcademyTestsTest, self).create(values)
        result.resequence()

        return result


    # @api.multi
    def write(self, values):
        """ Update all record(s) in recordset, with new value comes as {values}
            @param values: dict of new values to be set

            @return: True on success, False otherwise
        """

        result = super(AcademyTestsTest, self).write(values)
        self.resequence()

        return result



    def resequence(self):
        """ This updates the sequence of the questions into the test
        """

        # order_by = 'sequence ASC, write_date ASC, create_date ASC, id ASC'
        # rel_domain = [('test_id', '=', self.id)]
        # rel_obj = self.env['academy.tests.test.question.rel']
        # rel_set = rel_obj.search(rel_domain, order=order_by)

        for record in self:
            rel_set = record.question_ids.sorted()

            index = 1
            for rel_item in rel_set:
                rel_item.write({'sequence': index})
                index = index + 1

    def shuffle(self):
        qpositions = list(range(0, len(self.question_ids)))
        sequence = 1

        random_shuffle(qpositions)

        for qposition in qpositions:
            self.question_ids[qposition].sequence = sequence
            sequence += 1

        for question in self.question_ids:
            print(question.id, question.sequence)
