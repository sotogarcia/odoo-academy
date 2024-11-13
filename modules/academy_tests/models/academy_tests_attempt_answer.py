# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswer

This module contains the academy.tests.attempt.answer Odoo model which stores
all academy tests attempt answer attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import TRUE_DOMAIN

from logging import getLogger

_logger = getLogger(__name__)


USER_ACTIONS = [
    ('blank', 'Blank answer'),
    ('doubt', 'Unsure answer'),
    ('answer', 'Sure answer'),
]


def _made_check():
    case1 = '("user_action" = \'blank\' and "answer_id" IS NULL)'
    case2 = '("user_action" <> \'blank\' and "answer_id" IS NOT NULL)'

    return 'CHECK({} or {})'.format(case1, case2)


class AcademyTestAttemptAnswer(models.Model):
    """ Logs all student answers in a test attempt, even if later he
    change it by another answer
    """

    _name = 'academy.tests.attempt.answer'
    _description = u'Academy tests attempt answer'

    _inherit = ['academy.abstract.attempt.answer']

    _rec_name = 'id'
    _order = 'instant DESC'

    prevalence = fields.Integer(
        string='Prevalence',
        required=True,
        readonly=True,
        index=True,
        default=9999,
        help='Indicates the prevalence order of the answer.'
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    attempt_id = fields.Many2one(
        string='Attempt',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the attempt which is being done',
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('attempt_id')
    def _onchange_attempt_id(self):
        test_id = self.attempt_id.test_id
        return {
            'domain': {
                'question_link_id': [('test_id', '=', test_id.id)]
            }
        }

    question_link_id = fields.Many2one(
        string='Question link',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question that has been answered',
        comodel_name='academy.tests.test.question.rel',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('question_link_id')
    def _onchange_question_link_id(self):
        question_id = self.question_link_id.question_id

        return {
            'domain': {
                'answer_id': [('question_id', '=', question_id.id)]
            }
        }

    link_sequence = fields.Integer(
        string='Sequence',
        related='question_link_id.sequence',
        store=True
    )

    answer_id = fields.Many2one(
        string='Answer',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the answer which has been selected by user',
        comodel_name='academy.tests.answer',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    is_correct = fields.Boolean(
        string='Is correct',
        readonly=True,
        index=True,
        related='answer_id.is_correct'
    )

    instant = fields.Datetime(
        string='Instant',
        required=True,
        readonly=False,
        index=False,
        default=fields.datetime.now(),
        help=False
    )

    user_action = fields.Selection(
        string='User action',
        required=True,
        readonly=False,
        index=False,
        default='blank',
        help='What did the user do?',
        selection=USER_ACTIONS
    )

    @api.onchange('user_action')
    def _onchange_user_action(self):
        for record in self:
            if record.user_action == 'blank':
                record.answer_id = None

    question_id = fields.Many2one(
        string='Question',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='question_link_id.question_id'
    )

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'check_blank_answer',
            _made_check(),
            _(u'Field answer_id is mandatory except for blanks')
        ),
        (
            'positive_prevalence',
            'CHECK(prevalence > 0)',
            'Prevalence must be a positive number'
        ),
    ]

    # -------------------------------------------------------------------------
    # Overridden Non-CRUD Methods
    # -------------------------------------------------------------------------

    @api.depends('answer_id', 'user_action')
    def name_get(self):
        result = []
        for record in self:
            if isinstance(record.id, models.NewId):
                name = _('New attempt answer')
            else:
                answer = record.answer_id.name or _('Answer')
                action = record.user_action or _('Blank')
                name = '{} - {} - #{}'.format(answer, action, record.id)

            result.append((record.id, name))

        return result

    # -------------------------------------------------------------------------
    # CRUD Methods and Their Helpers
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """ Overridden method 'create'
        """
        self._unset_answer_id_for_blank_entries(vals_list)

        parent = super(AcademyTestAttemptAnswer, self)
        result = parent.create(vals_list)

        if not self._is_prevalence_disabled():
            result.update_prevalence()

        return result

    def write(self, values):
        """ Remove answer_id when user action is True
        """

        self._unset_answer_id_for_blank_entries(values)

        parent = super(AcademyTestAttemptAnswer, self)
        result = parent.write(values)

        if self._is_prevalence_update_required(values):
            self.update_prevalence()

        return result

    def unlink(self):
        """ Overridden method 'unlink'
        """

        id_pairs = self._get_id_pairs()

        parent = super(AcademyTestAttemptAnswer, self)
        result = parent.unlink()

        if not self._is_prevalence_disabled():
            self.update_prevalence(id_pairs)

        return result

    @api.model
    def _unset_answer_id_for_blank_entries(self, vals_list):
        if isinstance(vals_list, dict):  # Single item
            vals_list = [vals_list]

        for values in vals_list:
            user_action = values.get('user_action', False)
            if user_action == 'blank':
                values['answer_id'] = None

    # -------------------------------------------------------------------------
    # Update prevalence
    # -------------------------------------------------------------------------

    @api.model
    def _is_prevalence_update_required(self, values):
        disabled = self.env.context.get('disable_prevalence_update', False)
        involved = set(['attempt_id', 'question_link_id', 'active', 'instant'])

        return not disabled and values and (involved & values.keys())

    @api.model
    def _is_prevalence_disabled(self):
        return self.env.context.get('disable_prevalence_update', False)

    def _get_id_pairs(self):
        id_pairs = []
        for record in self:
            if not record.attempt_id or not record.question_link_id:
                message = (f'Attempt answer {record.id} requires a valid '
                           f'attempt/question-link pair.')
                _logger.warning(message)
                continue

            id_pair = (record.attempt_id.id, record.question_link_id.id)
            id_pairs.append(id_pair)

        return id_pairs

    @staticmethod
    def _format_id_pairs(id_pairs):
        if not id_pairs:
            result = "(0, 0)"
        else:
            result = ', '.join(f'({pair[0]}, {pair[1]})' for pair in id_pairs)

        return result

    @api.model
    def reconcile_all(self):
        record_set = self.search(TRUE_DOMAIN)
        record_set.update_prevalence()

    def update_prevalence(self, id_pairs=False):
        sql_pattern = '''
            WITH targets AS (
                SELECT
                    attempt_id,
                    question_link_id
                FROM (
                    VALUES
                    {id_pairs}
                ) AS src ( attempt_id, question_link_id )
            ), answer_prevalence AS (
                SELECT
                    ans."id",
                    ROW_NUMBER ( ) OVER ( wnd ) AS prevalence
                FROM
                    academy_tests_attempt_answer AS ans
                INNER JOIN targets AS tgs ON tgs.attempt_id = ans.attempt_id
                    AND tgs.question_link_id = ans.question_link_id
                WINDOW wnd AS (
                        PARTITION BY ans.attempt_id,
                        ans.question_link_id
                    ORDER BY
                        ans.attempt_id,
                        ans.question_link_id,
                        ans.active DESC NULLS LAST,
                        ans.instant DESC,
                        ans.create_date DESC
                )
            )
            UPDATE academy_tests_attempt_answer AS ans
            SET prevalence = ap.prevalence
            FROM
                answer_prevalence AS ap
            WHERE
                ans."id" = ap."id" RETURNING attempt_id,
                question_link_id;
        '''

        if id_pairs is False:
            id_pairs = self._get_id_pairs()

        if id_pairs:
            id_pairs_str = self._format_id_pairs(id_pairs)
            sql = sql_pattern.format(id_pairs=id_pairs_str)

            message = f'update_prevalence([{id_pairs_str}])'
            _logger.debug(message)

            cursor = self.env.cr
            cursor.execute(sql)
