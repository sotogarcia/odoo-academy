# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.osv.expression import AND


_logger = getLogger(__name__)


class AcademyTestsCategorizacionWizard(models.TransientModel):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.categorization.wizard'
    _description = u'academy.tests.categorization.wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    show_topic = fields.Boolean(
        string='Topic',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show topic field'
    )

    show_versions = fields.Boolean(
        string='Versions',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show versions field'
    )

    show_categories = fields.Boolean(
        string='Categories',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show categories field'
    )

    show_level = fields.Boolean(
        string='Level',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to show level field'
    )

    show_type = fields.Boolean(
        string='Type',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to show type field'
    )

    show_tags = fields.Boolean(
        string='Tags',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to show tags field'
    )

    # filter_ids = fields.Many2many(
    #     string='Favourites',
    #     required=False,
    #     readonly=False,
    #     index=False,
    #     default=None,
    #     help='Choose filters will be used in view',
    #     comodel_name='ir.filters',
    #     relation='academy_tests_manual_categorization_wizard_ir_filters_rel',
    #     column1='wizard_id',
    #     column2='filter_id',
    #     domain=lambda self: self.domain_filter_ids(),
    #     context={},
    #     limit=None
    # )

    default_filter = fields.Boolean(
        string='Default',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to apply default filter'
    )

    @api.onchange('show_topic')
    def _onchange_topic_id(self):
        if self.show_topic:
            self.show_versions = True
            self.show_categories = True

    @staticmethod
    def _merge_dics(x, y):
        z = x.copy()   # start with keys and values of x
        z.update(y)    # modifies z with keys and values of y

        return z

    @staticmethod
    def _parse_dict(expresion):
        result = {}

        try:
            result = eval(expresion)
        except Exception as ex:
            _logger.warning(ex)

        return result

    def _get_last_used_wizard(self):
        wizard_set = self.env[self._name]

        context = self.env.context or {}
        uid = context.get('uid', False)

        if uid:
            domain = [('create_uid', '=', uid)]
            order = 'write_date DESC, create_date DESC'

            wizard_set = self.search(domain, limit=1, order=order)

        return wizard_set

    @api.model
    def default_get(self, fields):
        _super = super(AcademyTestsCategorizacionWizard, self)

        last_wizard = self._get_last_used_wizard()
        defaults = _super.default_get(fields)

        if last_wizard:
            for key in defaults.keys():
                defaults[key] = getattr(last_wizard, key)

        # if last_wizard and last_wizard.filter_ids:
        #     filter_ids = last_wizard.filter_ids.mapped('id')
        #     defaults['filter_ids'] = [(6, 0, filter_ids)]

        return defaults

    # def domain_filter_ids(self):
    #     model = 'academy.tests.question'

    #     context = self.env.context or {}
    #     uid = context.get('uid', -1)

    #     return [('user_id', '=', uid), ('model_id', '=', model)]

    def _compute_context_question_domain(self):
        domain = []
        context = self.env.context

        active_model = context.get('active_model', False)
        active_ids = context.get('active_ids', [])
        active_id = context.get('active_id', [])

        if active_ids and active_model:
            if active_model == 'academy.tests.question':
                domain = [('id', 'in', active_ids)]
            if active_model == 'academy.tests.test':
                domain = [('id', 'in', active_ids)]
                item_set = self.env[active_model]
                item_set = item_set.search(domain)

                target_ids = item_set.mapped('question_ids.question_id.id')
                domain = [('id', 'in', target_ids)]

            elif active_model == 'academy.tests.test.question.rel':
                domain = [('id', 'in', active_ids)]
                item_set = self.env[active_model]
                item_set = item_set.search(domain)

                target_ids = item_set.mapped('question_id.id')
                domain = [('id', 'in', target_ids)]

        if active_id and active_model == 'academy.tests.test':
            item_set = self.env[active_model]
            item_set = item_set.browse(active_id)
            target_ids = item_set.mapped('question_ids.question_id.id')
            domain = [('id', 'in', target_ids)]

        return domain

    def show_view(self):

        act_name = 'action_academy_tests_manual_categorization_act_window'
        view_name = 'view_academy_tests_manual_question_categorization_tree'

        self.ensure_one()

        context = self.env.context.copy() or {}
        domain = self._compute_context_question_domain()

        context['hide_topic'] = not (self.show_topic is True)
        context['hide_versions'] = not (self.show_versions is True)
        context['hide_categories'] = not (self.show_categories is True)
        context['hide_level'] = not (self.show_level is True)
        context['hide_type'] = not (self.show_type is True)
        context['hide_tags'] = not (self.show_tags is True)

        action = self.env.ref('academy_tests.{}'.format(act_name))
        action_context = self._parse_dict(action.context)

        adomain = eval(action.domain)
        if adomain:
            domain = AND([adomain, domain])

        view_item = self.env.ref('academy_tests.{}'.format(view_name))

        if self.default_filter:
            context.update({"search_default_my_own_available_questions": 1})

        return {
            'type': 'ir.actions.act_window',
            'name': action.name,
            'view_mode': action.view_mode,
            'view_id': action.view_id,
            'res_model': action.res_model,
            'view_id': view_item.id,
            'target': 'main',
            'domain': domain,
            'context': self._merge_dics(action_context, context)
        }
