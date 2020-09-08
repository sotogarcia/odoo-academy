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

    overwrite = fields.Selection(
        string='Overwrite',
        required=True,
        readonly=False,
        index=False,
        default='0',
        help='Check it to unlink existing questions before append new',
        selection=[
            ('0', 'None'),
            ('3', 'Questions'),
            ('5', 'Test info'),
            ('7', 'All')
        ]
    )

    shuffle = fields.Boolean(
        string='Shuffle',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to sort the questions randomly'
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
        string='Base template',
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
        default=lambda self: self.default_random_wizard_template_id(),
        help=False,
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    save = fields.Boolean(
        string='Save changes',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to save wizard data as template'
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
        """ Create a new set of lines will be used in inherited field. This
        uses name of the current user and timestamp to make record name and
        it sets active to False.
        """

        user_obj = self.env['res.users']
        user_set = user_obj.browse(self.env.context['uid'])

        name = '{} - {}'.format(
            user_set.name,
            fields.Datetime.context_timestamp(
                self, timestamp=datetime.now())
        )
        values = {'active': False, 'name': name}

        lineset_obj = self.env['academy.tests.random.template']
        lineset_item = lineset_obj.create(values)

        return lineset_item.id


    def default_random_wizard_template_id(self):
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        if (active_model == 'academy.tests.random.template' and active_ids):
            return active_ids[0]

        return None
        # template_obj = self.env['academy.tests.random.template']
        # self.random_wizard_template_id = template_obj.browse(active_ids[0])
        # self._onchange_random_wizard_template_id()

    @api.onchange('random_wizard_template_id')
    def _onchange_random_wizard_template_id(self):

        self.ensure_one()

        if self.random_wizard_template_id:
            self._merge_info_from_choosen_template()

            ids = []
            parent_id = self.random_template_id.id

            for line_item in self.random_wizard_template_id.random_line_ids:
                new_line = line_item.copy({'random_template_id': parent_id})
                ids.append(new_line.id)

            self.random_line_ids = [(6, None, ids)]

            self.name = self.random_wizard_template_id.name
            self.description = self.random_wizard_template_id.description


    def _merge_info_from_choosen_template(self):
        """ Reads
        """
        template = self.random_wizard_template_id
        wizard_fields = []
        for fname, field in self._fields.items():
            if hasattr(field, 'wizard'):
                wizard_fields.append(fname)

        for field in wizard_fields:
            value = getattr(template, field)
            setattr(self, field, value)


    # -------------------------------- CRUD -----------------------------------

    def unlink(self):
        """ Delete all record(s) from recordset

            @return: True on success, False otherwise
        """

        message = 'Garbage collector: removing random template {}'
        _logger.info(message.format(message))

        if self._inherited_line_set_is_no_longer_needed():
            self._remove_inherited_line_set()

        result = super(AcademyTestsRandomWizard, self).unlink()

        return result


    # -------------------------- AUXILIARY METHODS ----------------------------


    def _collect_garbage(self):
        """ Each one of used wizards creates at least a set of lines, this
        should be removed by garbage collector when it removes this parent
        transient model but if user cancels wizard transiend model is not
        strored but the set lines already exists.
        This method removes unactive sets of lines al all related records.
        """

        lineset_domain = [('active', '=', False)]
        lineset_obj = self.env['academy.tests.random.template']
        lineset_set = lineset_obj.search(
            lineset_domain, offset=0, limit=None, order=None, count=False)

        lineset_ids = lineset_set.mapped('id')

        line_domain = [('random_template_id', 'in', lineset_ids)]
        line_obj = self.env['academy.tests.random.line']
        line_set = line_obj.search(
            line_domain, offset=0, limit=None, order=None, count=False)

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


    def append_questions(self):
        """ Calls action by each related line
        """

        self.ensure_one()

        template = self.random_template_id
        template.append_questions(self.test_id, self.overwrite)

        if self.shuffle:
            self.test_id.shuffle()


    def _remove_inherited_line_set(self):
        """ Removes inherited line set. This method will be called by wizard
        unlink method to ensure line set and its lines are removed too.
        """
        self._remove_lines_from_set(self.random_template_id)
        self.random_template_id.unlink()
