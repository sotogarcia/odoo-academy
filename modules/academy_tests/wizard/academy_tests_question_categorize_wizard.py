# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Question Categorize Wizard

This module contains the academy.tests.question.categorize.wizard an unique
Odoo transient model which contains all the model attributes and behavior.

This model is a wizard to allow to select and categorize questions

Classes:
    AcademyTestsQuestionCategorizeWizard: This is the unique model class in
    this module, it defines a wizard its attributes and related behavior.

Todo:
    * MANY2MANY_ACTIONS should have `Remove` option. This will be delicate
    when the wizard works with categories.
    - [ ] required fields in view when checkbox is set to true

"""


from logging import getLogger
from operator import itemgetter

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


WIZARD_STATES = [
    ('step1', 'Targets'),
    ('step2', 'Batch'),
]

MANY2MANY_ACTIONS = [
    ('new', 'Add'),
    ('sub', 'Replace'),
]

VALIDATION_ERROR = _('You have chosen to change {target}, so you must fill in '
                     'the related fields')


# pylint: disable=locally-disabled, R0903,W0212
class AcademyTestsQuestionCategorizeWizard(models.TransientModel):
    """ This model is the representation of the academy tests question
    categorize wizard
    """

    _name = 'academy.tests.question.categorize.wizard'
    _description = u'Academy tests, question categorize wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_question_ids(),
        help=False,
        comodel_name='academy.tests.question',
        relation='academy_tests_question_categorize_question_rel',
        column1='question_categorize_wizard_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Choose topic will be set to selected questions',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    change_topic = fields.Boolean(
        string='Change the topic',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='If checked topic will be set to selected questions'
    )

    topic_version_ids = fields.Many2many(
        string='Topic versions',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_topic_version_ids(),
        help='Choose which versions of the topic this question belongs to',
        comodel_name='academy.tests.topic.version',
        relation='academy_tests_question_categorize_topic_version_rel',
        column1='question_import_id',
        column2='topic_version_id',
        domain=[],
        context={},
        limit=None
    )

    topic_version_action = fields.Selection(
        string='Version action',
        required=False,
        readonly=False,
        index=False,
        default='new',
        help='Choose how to set versions',
        selection=MANY2MANY_ACTIONS
    )

    category_ids = fields.Many2many(
        string='Categories',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose categories will be set to selected questions',
        comodel_name='academy.tests.category',
        relation='academy_tests_question_categorize_category_rel',
        column1='question_categorize_wizard_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None
    )

    category_action = fields.Selection(
        string='Category action',
        required=False,
        readonly=False,
        index=False,
        default='new',
        help='Choose how to set categories',
        selection=MANY2MANY_ACTIONS
    )

    type_id = fields.Many2one(
        string='Type',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose type will be set to selected questions',
        comodel_name='academy.tests.question.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    change_type = fields.Boolean(
        string='Change the type',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='If checked type will be set to selected questions'
    )

    level_id = fields.Many2one(
        string='Difficulty',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose level will be set to selected questions',
        comodel_name='academy.tests.level',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    change_level = fields.Boolean(
        string='Change the difficulty',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='If checked level will be set to selected questions'
    )

    tag_ids = fields.Many2many(
        string='Tags',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose tags will be set to selected questions',
        comodel_name='academy.tests.tag',
        relation='academy_tests_question_categorize_tag_rel',
        column1='question_categorize_wizard_id',
        column2='tag_id',
        domain=[],
        context={},
        limit=None
    )

    tag_action = fields.Selection(
        string='Change the tag',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Choose how to set tags',
        selection=MANY2MANY_ACTIONS
    )

    state = fields.Selection(
        string='State',
        required=False,
        readonly=False,
        index=False,
        default='step1',
        help='Current wizard step',
        selection=WIZARD_STATES
    )

    autocategorize = fields.Boolean(
        string='Autocategorize',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check to autocategorize questions'
    )

    status = fields.Selection(
        string='Status',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Switch question status',
        selection=[
            ('draft', 'Draft'),
            ('ready', 'Ready')
        ]
    )

    authorship = fields.Selection(
        string='Authorship',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        selection=[
            ('own', 'My own'),
            ('third', 'Third-party')
        ]
    )

    # ------------------------------ DEFAULTS ---------------------------------

    def default_question_ids(self):
        """ It computes default question list loading all has been selected
        before wizard opening
        """

        ids = self.env.context.get('active_ids', [])

        return [(6, None, ids)] if ids else False

    # ------------------------------- EVENTS ----------------------------------

    @api.onchange('topic_id')
    def _onchange_topic_id(self):
        self.category_ids = [(5, None, None)]
        self.topic_version_ids = self.default_topic_version_ids()

    @api.onchange('state')
    def _onchange_state(self):
        self._ensure_state()

    @api.onchange('question_ids')
    def _onchange_question_ids(self):

        if not hasattr(self, '_origin'):
            return

        if self._origin.question_ids:
            return

        question_set = self.question_ids

        self.topic_id = self._most_repeated(question_set, 'topic_id')
        self.level_id = self._most_repeated(question_set, 'level_id')
        self.type_id = self._most_repeated(question_set, 'type_id')

        cat_ids = question_set.mapped('category_ids').mapped('id')
        val_ids = self.topic_id.mapped('category_ids').mapped('id')
        category_ids = [cid for cid in cat_ids if cid in val_ids]
        if category_ids:
            self.category_ids = [(6, None, category_ids)]

        tag_ids = question_set.mapped('tag_ids').mapped('id')
        if tag_ids and len(tag_ids) <= 10:
            self.tag_ids = [(6, None, tag_ids)]

    # --------------------------- PUBLIC METHODS ------------------------------

    def update_targets(self):
        # pylint: disable=locally-disabled, E1101, C0325
        """ Perform the update
        """

        self.ensure_one()
        self._validate_form(raise_error=True)

        values = self._get_values()

        if values:
            self.question_ids.write(values)

        if self.autocategorize:
            abstract = self.env['academy.abstract.import.export']
            for question_item in self.question_ids:
                topic_id = question_item.topic_id
                abstract.auto_set_categories(question_item, topic_id)

    # -------------------------- AUXILIARY METHODS ----------------------------

    def default_topic_version_ids(self):
        """ This returns all versions for the chosen topic
        """
        return self.topic_id.last_version()

    def _ensure_state(self):
        """ Check given step returning it if is valid or the mayor valid step
        otherwise
        """

        valid = [WIZARD_STATES[0][0]]
        result = True

        if self.question_ids:
            valid.append(WIZARD_STATES[1][0])

        # if self.topic_id or self.category_ids:
        #     valid.append(WIZARD_STATES[2][0])

        if self.state not in valid:
            self.state = valid[-1]
            result = False

        return result

    def _reload_on_step3(self):
        """ Builds an action which loads again transient model record using
        'step3' as state
        @note: actually this method is not used
        """
        self.write({'state': 'step3'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.tests.question.categorize.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new'
        }

    def _validate_form(self, raise_error=True):
        """ Check if all required wizard field values have been filled by user.
            Required fiels are not always the same, this depends on the
            checkboxes that the user has activated
        """

        target = None

        category_filled = self.category_ids and self.category_action
        version_filled = self.topic_version_ids and self.topic_version_action

        if self.change_topic and not (self.topic_id and category_filled):
            target = _('topic and categories')
        if self.change_topic and not (self.topic_id and version_filled):
            target = _('topic and versions')
        elif self.change_type and not self.type_id:
            target = _('type')
        elif self.change_level and not self.level_id:
            target = _('level')
        elif self.tag_action == 'new' and not self.tag_ids:
            target = _('tag')

        if target and raise_error:
            raise ValidationError(VALIDATION_ERROR.format(target=target))

        return target is None

    def _append_leaf(self, values, fname, replace=False):
        """ Appends a valid leaf to a values dictionary. This gets the value
        from a wizard field which have the same name as in a question model.
        - This fields can be Many2one or Many2many
        - If the field has not value, remove operation will be added.

        @param values (dict): dictionary to will leaf will be added
        @param fname (str): name of the field
        @param replace (boolean): if is set to `True` previous related values
        will be removed (unlinked) before set new ones, otherwise, the previous
        Many2many records will be kept on.
        """

        recordset = getattr(self, fname)
        field = self._fields[fname]

        if isinstance(field, fields.Many2one):
            if recordset:
                values.update({fname: recordset.id})
            elif replace:
                values.update({fname: None})

        elif isinstance(field, fields.Many2many):
            _ids = recordset.mapped('id')
            if replace:
                if _ids:
                    values.update({fname: [(6, None, _ids)]})
                else:
                    values.update({fname: [(5, None, None)]})
            else:
                values.update({fname: [(4, _id, None) for _id in _ids]})

    def _append_leaf_to_remove_unsuited(self, fname, values):
        """ Categories and versions are related to a topic, previous
        question recordset can be incompatible with current topic, this
        method search for non compatible categories and versions to append
        the needed leafs to remove them.

        @param fname (string): field name (category_ids or topic_version_ids)
        @parm values (dict): values dictionary will be updated
        """

        old_ids = self.question_ids.mapped(fname).mapped('id')
        valid_ids = self.topic_id.mapped(fname).mapped('id')

        for _id in old_ids:
            if _id not in valid_ids:
                values[fname].append((3, _id, None))

    def _get_values(self):
        values = {}

        if self.change_topic:
            self._append_leaf(values, 'topic_id')

            replace = (self.category_action == 'sub')
            self._append_leaf(values, 'category_ids', replace=replace)
            self._append_leaf_to_remove_unsuited('category_ids', values)

            replace = (self.topic_version_action == 'sub')
            self._append_leaf(values, 'topic_version_ids', replace=replace)
            self._append_leaf_to_remove_unsuited('topic_version_ids', values)

        if self.change_type:
            self._append_leaf(values, 'type_id')

        if self.change_level and self.level_id:
            self._append_leaf(values, 'level_id')

        if self.tag_action:
            replace = (self.tag_action == 'sub')
            self._append_leaf(values, 'tag_ids', replace=replace)

        if self.status:
            values['status'] = self.status

        if self.authorship:
            values['authorship'] = (self.authorship == 'own')

        return values

    @staticmethod
    def _increment_item_counter(items_dict, item_key):
        """ Incrents value for existing key or appends new with value set to 1

        @param items_dict(dict): dictionary with integers in items value
        @param iem_key: name of key will be incremented or appended
        """

        if item_key in items_dict.keys():
            items_dict[item_key] = items_dict[item_key] + 1
        else:
            items_dict[item_key] = 1

    def _most_repeated(self, recordset, fname):
        """ Search for most repeated value for given field in a recordset
        @param recordset: recordset in which value will be searched
        @param fname (str): name of the field will be used in search
        """

        field = self._fields[fname]
        repeated = {}

        if isinstance(field, fields.Many2one):
            for item in recordset:
                value_set = getattr(item, fname)
                if value_set:
                    self._increment_item_counter(repeated, value_set.id)

        elif isinstance(field, (fields.Many2many, fields.One2many)):
            for item in recordset:
                value_set = getattr(item, fname)
                for value_item in value_set:
                    self._increment_item_counter(repeated, value_item.id)

        else:
            for item in recordset:
                value = getattr(item, fname)
                self._increment_item_counter(repeated, value)

        # https://stackoverflow.com/questions/268272/
        return max(repeated.items(), key=itemgetter(1))[0] if repeated else False
