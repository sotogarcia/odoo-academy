# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Random Wizard

This module contains the academy.tests.random.wizard an unique Odoo model
which contains all Academy Tests Random Wizard attributes and behavior.

This wizard is a transient model and thus this will be deleted by garbage
collector, but its data can be saved before by checking the `save` field.
In this case, two things can happen:
    1. There is a related external template (`random_wizard_template_id`):
    then wizard data will be transfered to this related template. Current
    inherited `random_template_id` set of lines will be deleted when
    garbage collector calls `unlink` method.
    2. There is not a related template  (`random_wizard_template_id`):
    then the inherited `random_template_id` set of lines will be used
    as template.


TODO
- [ ] Method _onchange_random_wizard_template_id changes active value,
perheaps this action is wrong
- [ ] Method _onchange_random_wizard_template_id removes current lines
when template is unlinked, is this action was removed then current lines
will be kept in new set allowing to create new template with a copy from
old template.
- [ ] Full current save tamplate behavior is called from CRUD methods,
this should be called from `append_questions` method *before* performs
the action.

"""


from logging import getLogger
from datetime import datetime
from pprint import pprint

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903, W0201
class AcademyTestsRandomWizard(models.TransientModel):
    """ This model is the representation of the academy tests random wizard

    Fields:
      name (Char)       : Human readable name which will identify each record
      description (Text): Something about the record or other information which
      has not an specific defined field to store it.
      active (Boolean)  : Checked do the record will be found by search and
      browse model methods, unchecked hides the record.

    """


    _name = 'academy.tests.random.wizard'
    _description = u'Academy tests, random wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    _inherits = {'academy.tests.random.template': 'random_template_id'}

    overwrite = fields.Boolean(
        string='Overwrite',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check this to unlink existing questions before append new'
    )

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=False,
        help='Test to which questions will be added',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        default=lambda self: self.default_test_id()
    )

    random_template_id = fields.Many2one(
        string='Template',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_random_template_id(),
        help=False,
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    random_wizard_template_id = fields.Many2one(
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

    save = fields.Boolean(
        string='Save changes',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check to save wizard data as template'
    )


    last_update = fields.Datetime(
        string='Last update',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Last template update',
        compute=lambda self: self.compute_last_update()
    )


    # ----------------- AUXILIARY FIELDS METHODS AND EVENTS -------------------


    def default_test_id(self):
        """ It computes default question list loading all has been selected
        before wizard opening
        """
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        if (active_model == 'academy.tests.test' and active_ids):
            return active_ids[0]

        return None


    def default_random_template_id(self):
        """ Creates a new set of lines will be used in inherited field. This
        uses name of the current user and timestamp to make record name and
        it sets active to False.
        """

        user_obj = self.env['res.users']
        user_set = user_obj.browse(self.env.context['uid'])

        name = '{} - {}'.format(
            user_set.name,
            fields.Datetime.context_timestamp(self, timestamp=datetime.now())
        )
        values = {'active': False, 'name': name}

        lineset_obj = self.env['academy.tests.random.template']
        lineset_item = lineset_obj.create(values)

        return lineset_item.id


    # @api.multi
    @api.depends('random_wizard_template_id')
    def compute_last_update(self):
        """ Change value to last_update field to show choosen template
        write_date
        """

        for record in self:
            record.last_update = self.random_wizard_template_id.write_date


    @api.onchange('random_wizard_template_id')
    def _onchange_random_wizard_template_id(self):
        # print('hola')

        # if self.random_wizard_template_id:

        #     ids = []
        #     parent_id = self.random_template_id.id
        #     for line_item in self.random_wizard_template_id.random_line_ids:
        #         new_line = line_item.copy({'random_wizard_id': parent_id})
        #         ids.append(new_line.id)

        #     self.random_template_id.random_line_ids = [(6, None, ids)]

        #     self.name = self.random_wizard_template_id.name
        #     self.description = self.random_wizard_template_id.description

        self.ensure_one()

        self.last_update = self.random_wizard_template_id.write_date

        if self.random_wizard_template_id:

            ids = []
            parent_id = self.random_template_id.id
            for line_item in self.random_wizard_template_id.random_line_ids:
                new_line = line_item.copy({'random_wizard_id': parent_id})
                ids.append(new_line.id)
                print(new_line)

            self.random_line_ids = [(6, None, ids)]

            self.name = self.random_wizard_template_id.name
            self.description = self.random_wizard_template_id.description




    # -------------------------------- CRUD -----------------------------------

    # @api.multi
    def unlink(self):
        """ Delete all record(s) from recordset

            @return: True on success, False otherwise
        """

        if self._inherited_line_set_is_no_longer_needed():
            self._remove_inherited_line_set()

        result = super(AcademyTestsRandomWizard, self).unlink()

        return result


    # ---------------------------- PUBIC METHODS ------------------------------

    # @api.multi
    def append_questions(self):
        """ Calls action by each related line
        """

        self.ensure_one()

        self._overwrite_pre_requirements()

        values = self._get_base_values()
        current_leaf = self._leaf_to_exclude_current_questions()
        question_set = self.random_line_ids.perform_search(current_leaf)
        leafs = self._make_insert_leafs(question_set, values)
        self._write_leafs(leafs)

        self._update_template()

        self._collect_garbage()


    # -------------------------- AUXILIARY METHODS ----------------------------

    def _leaf_to_exclude_current_questions(self):
        current_leaf = None

        if not self.overwrite and self.test_id and self.test_id.question_ids:
            question_ids = self.test_id.question_ids.mapped('question_id')
            current_ids = question_ids.mapped('id')
            current_leaf = [('id', 'not in', current_ids)]

        return current_leaf

    def _overwrite_pre_requirements(self):
        if self.overwrite:
            self.test_id.write({
                'question_ids': [(5, 0, 0)]
            })

        return self.test_id.question_ids


    def _compute_base_sequence_value(self):
        sequences = self.test_id.question_ids.mapped('sequence') or [0]
        return (max(sequences)) + 0 if not self.overwrite else 0


    def _get_base_values(self):
        return {
            'test_id': self.test_id.id,
            'question_id': None,
            'sequence': self._compute_base_sequence_value(),
            'active': True
        }


    def _update_template(self):
        result = self.random_template_id

        if self.save:
            if self.random_wizard_template_id:
                self.active = False
                self._update_template_with(self)
                result = self.random_wizard_template_id
            else:
                self.active = True
        else:
            self.active = False

        return result


    @staticmethod
    def _make_insert_leafs(question_set, base_values):
        leafs = []
        values = base_values.copy()
        for question in question_set:
            values['question_id'] = question.id
            values['sequence'] = values['sequence'] + 1

            leafs.append((0, None, values.copy()))

        return leafs


    def _write_leafs(self, leafs):
        return self.test_id.write({
            'question_ids': leafs
        })


    def _collect_garbage(self):
        """ Each one of used wizards creates at least a set of lines, this
        should be removed by garbage collector when it removes this parent
        transient model but if user cancels wizard transiend model is not
        strored but the set lines already exists.
        This method removes unactive sets of lines al all related records.
        """

        lineset_domain = [('active', '=', False)]
        lineset_obj = self.env['academy.tests.random.template']
        lineset_set = lineset_obj.search(lineset_domain, \
            offset=0, limit=None, order=None, count=False)

        lineset_ids = lineset_set.mapped('id')

        line_domain = [('random_wizard_id', 'in', lineset_ids)]
        line_obj = self.env['academy.tests.random.line']
        line_set = line_obj.search(line_domain, \
            offset=0, limit=None, order=None, count=False)

        line_set.unlink()
        lineset_set.unlink()


    def _inherited_line_set_is_no_longer_needed(self):
        """ Check if lines in inherited line set should be removed
        """
        return not self.save or self.random_wizard_template_id


    @staticmethod
    def _remove_lines_from_set(source):
        """ This removes (erase from database) lines from line set

        @param source (academy.tests.reandom.wizard.set): wizard set
        which contains lines will be removed
        """

        line_set = source.random_line_ids
        actions = [(2, line.id, None) for line in line_set]
        source.random_line_ids = actions


    @staticmethod
    def _link_lines_to_set(target, source_ids):
        """ Link lines with given ids (source_ids) to an other line set.
        Lines and sets are related by a Many2one field, so when lines are
        linked to a new set also are unlinked from previous parent set.

        @target (academy.tests.random.template): line set to which lines
        will be attached
        @source_ids (list): list of line identifiers (`id`) will be used
        to perform action
        """

        actions = [(4, ID, None) for ID in source_ids]
        target.random_line_ids = actions


    def _remove_inherited_line_set(self):
        """ Removes inherited line set. This method will be called by wizard
        unlink method to ensure line set and its lines are removed too.
        """
        self._remove_lines_from_set(self.random_template_id)
        self.random_template_id.unlink()


    def _update_template_with(self, source=None):
        """ The related pre-existing template will be updated with the
        current wizard values.
        """

        # STEP 1: Updating set attributes
        template_item = source.random_wizard_template_id
        template_item.name = source.name
        template_item.description = source.description
        # -- Not proceed --> template_item.active = source.active

        # STEP 2: Replacing old lines with the new updated copies
        # pylint: disable=locally-disabled, E1101, W0201
        ids = [item.id for item in source.random_line_ids]
        self._remove_lines_from_set(template_item)
        self._link_lines_to_set(template_item, ids)

        return template_item

