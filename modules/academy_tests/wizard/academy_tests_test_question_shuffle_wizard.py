# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN
from odoo.exceptions import ValidationError

from logging import getLogger
from collections import defaultdict, deque
from random import shuffle


_logger = getLogger(__name__)


class AcademyTestsTestQuestionShuffleWizard(models.TransientModel):
    """
    This wizard allows users to reorder both the blocks and the questions 
    within a given test (`academy.tests.test`).

    It supports different shuffle scopes and defines how unassigned 
    questions (not linked to any block) should be handled.
    """

    _name = 'academy.tests.test.question.shuffle.wizard'
    _description = u'Academy tests test question shuffle wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    # - Field: question_rel_ids (default + onchange)
    # ------------------------------------------------------------------------

    question_rel_ids = fields.Many2many(
        string='Target links',
        required=False,
        readonly=True,
        index=False,
        default=lambda self: self._default_question_rel_ids(),
        help=False,
        comodel_name='academy.tests.test.question.rel',
        relation='academy_tests_test_question_shuffle_wizard_link_rel',
        column1='wizard_id',
        column2='link_id',
        domain=[],
        context={},
        limit=None
    )

    def _default_question_rel_ids(self):
        """Default getter for question_rel_ids based on context"""
        context = self.env.context

        rel_obj = self.env['academy.tests.test.question.rel']
        rel_set = rel_obj.browse()

        active_model = context.get('active_model', None)
        active_id = context.get('active_id', None)
        active_ids = context.get('active_ids', [])
        default_test_id = context.get('default_test_id', None)

        if not active_model and default_test_id:
            test = self.env['academy.tests.test'].browse(default_test_id)
            if test.exists():
                rel_set = test.question_ids

        elif active_model == 'academy.tests.test' and active_id:
            test = self.env['academy.tests.test'].browse(active_id)
            if test.exists():
                rel_set = test.question_ids

        elif active_model == 'academy.tests.test.question.rel' and active_ids:
            rel_set = rel_obj.browse(active_ids)

        return rel_set

    @api.onchange('question_rel_ids')
    def onchange_question_rel_ids(self):
        test_block_set = self.question_rel_ids.mapped('test_block_id')

        o2m_ops = [(5, 0, 0)]

        sequence = 1
        for test_block in self._get_question_rel_blocks():
            values = {'sequence': sequence, 'block_id': test_block._origin.id}
            o2m_op = (0, 0, values)
            o2m_ops.append(o2m_op)

        self.block_position_ids = o2m_ops

        block_ids = self.question_rel_ids.mapped('test_block_id').ids
        if block_ids:
            block_domain = [('block_id', 'in', block_ids)]
        else:
            block_domain = FALSE_DOMAIN

        return {
            'domain': {
                'block_position_ids': block_domain
            }
        }

    # - Field: question_rel_count (compute)
    # ------------------------------------------------------------------------

    question_rel_count = fields.Integer(
        string='Question rel count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='False',
        compute='_compute_question_rel_count'
    )

    @api.depends('question_rel_ids')
    def _compute_question_rel_count(self):
        for record in self:
            record.question_rel_count = len(record.question_rel_ids)

    # - Field: test_id (compute)
    # ------------------------------------------------------------------------

    test_id = fields.Many2one(
        string='Test',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_test_id'
    )

    @api.depends('question_rel_ids')
    def _compute_test_id(self):
        err = _('There are questions from more than one test.')
        for record in self:
            test_set = record.mapped('question_rel_ids.test_id')
            if len(test_set) > 1:
                raise ValidationError(err)
            record.test_id = test_set[0]
 
    # ------------------------------------------------------------------------
   
    block_position_ids = fields.One2many(
        string='Block positions',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Temporary list of blocks and their new positions within the test',
        comodel_name='academy.tests.test.question.block.position',
        inverse_name='wizard_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    # - Field: available_block_ids (compute)
    # ------------------------------------------------------------------------

    available_block_ids = fields.Many2many(
        string='Available blocks',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test.block',
        relation='academy_tests_test_question_shuffle_wizard_test_block_rel',
        column1='wizard_id',
        column2='block_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_available_block_ids'
    )

    @api.depends('block_position_ids')
    def _compute_available_block_ids(self):
        block_path = 'block_position_ids.block_id'
        for record in self:
            record.available_block_ids = record.mapped(block_path)
 
    # ------------------------------------------------------------------------
   
    shuffle_scope = fields.Selection(
        string='Shuffle scope',
        required=True,
        default='questions',
        selection=[
            ('questions', 'Questions'), 
            ('blocks', 'Blocks'),
            ('both', 'Both')
        ],
        help='Choose whether to shuffle the questions, the blocks, or both'
    )

    # - Field: unassigned_question_handling (onchange)
    # ------------------------------------------------------------------------

    unassigned_question_handling = fields.Selection(
        string='Unassigned questions',
        required=True,
        readonly=False,
        index=False,
        default='beginning',
        help='How to handle questions not linked to any block',
        selection=[
            ('beginning', 'Place at the beginning'), 
            ('end', 'Place at the end'),
            ('assign', 'Assign to block')
        ],
    )

    @api.onchange('unassigned_question_handling')
    def _onchange_unassigned_question_handling(self):
        if self.unassigned_question_handling != 'assign':
            self.assign_to_block_id = None

    # ------------------------------------------------------------------------

    assign_to_block_id = fields.Many2one(
        string='Assign to block',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Target block for unassigned questions, if applicable',
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    random_order = fields.Boolean(
        string='Random order',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='If enabled, the questions will be ordered randomly'
    )

    # -------------------------------------------------------------------------
    # CONSTRAINS
    # -------------------------------------------------------------------------

    @api.constrains("unassigned_question_handling")
    def _check_unassigned_question_handling(self):
        message = _(
            'You must select a target block when choosing '
            '"Assign to block" as the handling method for unassigned questions.'
        )

        for record in self:
            if (
                record.unassigned_question_handling == "assign"
                and not record.assign_to_block_id
            ):
                raise ValidationError(message)

    # -------------------------------------------------------------------------
    # PUBLIC METHOD
    # -------------------------------------------------------------------------

    def perform_action(self, reload_on_exit=True):
        for record in self:
            record._perform_action()

        if reload_on_exit:
            return {'type': 'ir.actions.client', 'tag': 'reload'}

        return True

    @api.model
    def create_from_recordset(self, record_set):
        """
        Create a shuffle wizard from a recordset, which may be either:
        - a single academy.tests.test record
        - a recordset of academy.tests.test.question.rel links
        """
        if not record_set:
            message = _('You must provide a non-empty recordset.')
            raise ValidationError(message)

        question_rel_set = self._get_question_links(record_set)
        if not question_rel_set:
            message = _('No question links found to populate the wizard.')
            raise ValidationError(message)

        context = dict(self.env.context or {})
        context.update({
            'active_model': 'academy.tests.test.question.rel',
            'active_ids': question_rel_set.ids
        })

        wizard = self.with_context(context).new({})
        wizard.onchange_question_rel_ids()
        wizard = wizard.create(wizard._convert_to_write(wizard._cache))

        return wizard

    # -------------------------------------------------------------------------
    # ORDERING AND SEQUENCING
    # -------------------------------------------------------------------------

    def _perform_action(self):
        """
        Reorders the question-test links based on the selected shuffle scope,
        and handles unassigned questions according to user configuration.
        """
        self.ensure_one()
        
        # Retrieve all selected question links. If empty, skip processing
        link_set = self.question_rel_ids
        if not link_set:
            _logger.info('No question links to reorder in shuffle wizard')
            return

        # Validate that all blocks in use are included in the wizard
        self._check_all_used_blocks_are_defined()

        # Random order is not allowed if any question has dependencies
        if self.random_order:
            self._check_dependencies_for_random_order()

        # Enforce dependency order: 
        # Dependent questions must follow their prerequisites
        if not self._check_is_topologically_sorted(link_set):
            link_set = self._sort_relations_by_dependency(link_set)

        # Separate unassigned and assigned links
        unassigned_links = link_set.filtered(lambda q: not q.test_block_id)
        assigned_links = link_set - unassigned_links

        sequence = 1

        # Reassign unassigned questions to a specific block if requested
        if self.unassigned_question_handling == 'assign':
            target_block = self.assign_to_block_id
            for link in unassigned_links:
                link.write({'test_block_id': target_block.id})

            # Now all are considered assigned
            assigned_links += unassigned_links
            unassigned_links = self.env['academy.tests.test.question.rel']

        # Place unassigned questions before the rest, if configured
        if self.unassigned_question_handling == 'beginning':
            sequence = self._write_sequence_ordered(unassigned_links, sequence)

        # Reorder the assigned links based on shuffle scope
        if self.shuffle_scope == 'questions':
            sequence = self._action_sort_questions(assigned_links, sequence)
        elif self.shuffle_scope == 'blocks':
            sequence = self._action_sort_blocks(assigned_links, sequence)
        elif self.shuffle_scope == 'both':
            sequence = self._action_sort_both(assigned_links, sequence)

        # Place unassigned questions after the rest, if configured
        if self.unassigned_question_handling == 'end':
            sequence = self._write_sequence_ordered(unassigned_links, sequence)

         # Refresh recordset in memory with new sequence order
        self.question_rel_ids = self.question_rel_ids.sorted('sequence')

    def _action_sort_questions(self, link_set, sequence):
        """
        Reassign sequence within each block, preserving the block order as 
        found in the link_set (first appearance). Questions within each block 
        are sorted by their previous sequence, unless random_order is enabled.
        """
        seen = set()
        ordered_blocks = []

        # Detect unique blocks in first-seen order
        for link in link_set:
            block = link.test_block_id
            if block and block.id not in seen:
                seen.add(block.id)
                ordered_blocks.append(block)

        # Reassign sequence within each block
        for block in ordered_blocks:
            block_link_set = link_set.filtered(
                lambda q: q.test_block_id == block
            )
            sequence = self._write_sequence_ordered(block_link_set, sequence)

        return sequence

    def _action_sort_blocks(self, link_set, sequence):
        """
        Use block order defined in wizard (unless random_order is True);
        questions within each block are sorted by their previous sequence,
        unless random_order is enabled.
        """
        # Get block order from wizard
        ordered_blocks = [pos.block_id for pos in self.block_position_ids]

        if self.random_order:
            shuffle(ordered_blocks)

        # Reassign sequence in block order
        for block in ordered_blocks:
            block_link_set = link_set.filtered(
                lambda q: q.test_block_id == block
            )
            sequence = self._write_sequence_ordered(block_link_set, sequence)

        return sequence

    def _action_sort_both(self, link_set, sequence):
        """
        Randomly reorder blocks and questions inside each block if random_order
        is True. Otherwise, use manual block order and sort questions by 
        previous sequence.
        """
        # Get user-defined block order
        ordered_blocks = [pos.block_id for pos in self.block_position_ids]

        if self.random_order:
            shuffle(ordered_blocks)

        # Reorder questions block by block
        for block in ordered_blocks:
            block_link_set = link_set.filtered(
                lambda q: q.test_block_id == block
            )
            sequence = self._write_sequence_ordered(block_link_set, sequence)

        return sequence

    def _write_sequence_ordered(self, link_set, sequence=1):
        """
        Reassigns sequence values to the given link_set.

        The links will be sorted according to self.random_order:
        - If True, the links are shuffled randomly.
        - If False, they are sorted by current sequence.

        :param link_set: Recordset or list of question links to reorder
        :param sequence: Starting sequence number
        :return: Final value of sequence after assigning
        """
        self.ensure_one()

        links = list(link_set)
        if self.random_order:
            shuffle(links)
        else:
            links.sort(key=lambda l: l.sequence)

        for link in links:
            link.write({'sequence': sequence})
            sequence += 1

        return sequence

    # -------------------------------------------------------------------------
    # EARLY VALIDATION
    # -------------------------------------------------------------------------

    def _check_all_used_blocks_are_defined(self):
        """
        Ensure that every block used in the selected question links
        is present in the defined block positions. Raise ValidationError if not.
        """
        self.ensure_one()

        used_block_ids = set(self.question_rel_ids.mapped('test_block_id.id'))
        defined_block_ids = set(self.block_position_ids.mapped('block_id.id'))

        missing_block_ids = used_block_ids - defined_block_ids
        if missing_block_ids:
            block_obj = self.env['academy.tests.test.block']
            missing_blocks = block_obj.browse(list(missing_block_ids))
            block_names = missing_blocks.mapped('display_name')

            message = _(
                'Some blocks used in the selected question links '
                'are not represented in the block position list:\n%s'
            )
            raise ValidationError(message % ', '.join(sorted(block_names)))

    @staticmethod
    def _check_is_topologically_sorted(rel_set):
        id_to_sequence = {rel.question_id.id: rel.sequence for rel in rel_set}

        for rel in rel_set:
            dep = rel.question_id.depends_on_id
            if dep and dep.id in id_to_sequence:
                if id_to_sequence[dep.id] > rel.sequence:
                    return False
        return True

    @staticmethod
    def _sort_relations_by_dependency(rel_set):
        """
        Return a recordset of academy.tests.test.question.rel ordered so that
        no question appears before the one it depends on.

        :param rel_set: recordset of academy.tests.test.question.rel
        :return: ordered recordset
        :raises ValueError: if circular dependency is detected
        """

        # Build ID -> rel record mapping
        question_map = {rel.question_id.id: rel for rel in rel_set}

        # Build graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        for rel in rel_set:
            dependent_id = rel.question_id.id
            dependency = rel.question_id.depends_on_id

            if dependency and dependency.id in question_map:
                graph[dependency.id].append(dependent_id)
                in_degree[dependent_id] += 1
            else:
                in_degree[dependent_id] += 0

        # Initialize queue with questions that have no dependencies
        queue = deque([qid for qid in in_degree if in_degree[qid] == 0])

        sorted_ids = []
        while queue:
            qid = queue.popleft()
            rel = question_map[qid]
            sorted_ids.append(rel.id)

            for neighbor in graph[qid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_ids) != len(rel_set):
            raise ValidationError(
                'Circular dependency detected among questions'
            )

        # Return recordset in the correct order
        return rel_set.browse(sorted_ids)

    def _check_dependencies_for_random_order(self):
        """
        Raise an error if random_order is enabled and any question has 
        dependencies.
        """
        self.ensure_one()

        dep_links = self.question_rel_ids.filtered(
            lambda rel: rel.question_id.depends_on_id
        )

        if dep_links:
            message = _(
                'Random order cannot be used when some questions '
                'depend on others.'
            )
            raise ValidationError(message)

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    def _get_question_rel_blocks(self):
        block_obj = self.env['academy.tests.test.block']
        block_ids = []

        for link in self.question_rel_ids:
            block = link.test_block_id
            if block and block.id not in block_ids:
                block_ids.append(block.id)

        return block_obj.browse(block_ids)

    @api.model
    def _get_question_links(self, record_set):
        rel_model = self.env['academy.tests.test.question.rel']
        model_name = record_set._name

        if model_name == 'academy.tests.test':
            if len(record_set) != 1:
                message = _('Only one test can be used to create the wizard.')
                raise ValidationError(message)
            return record_set.question_ids

        elif model_name == 'academy.tests.test.question.rel':
            return rel_model.browse(record_set.ids)

        message = _(
            'Invalid recordset type: expected test or question links, got %s'
        )
        raise ValidationError(message % model_name)

