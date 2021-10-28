# -*- coding: utf-8 -*-
""" AcademyTestsRandomTemplateScheduled

This module extends academy.tests.random.template and ir.cron to automate
test creation
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)

ACTION_CODE = '''
schedule_item = env['academy.tests.random.template.scheduled']
schedule_item = schedule_item.browse({})
schedule_item.new_test()
'''


class AcademyTestsRandomTemplateScheduled(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.random.template.scheduled'
    _description = u'Template scheduled task'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = ['mail.thread']

    _inherits = {'ir.cron': 'ir_cron_id'}

    template_id = fields.Many2one(
        string='Template',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Choose related tests random template',
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    ir_cron_id = fields.Many2one(
        string='Cron task',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Choose related cron task',
        comodel_name='ir.cron',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    one_by_enrolment = fields.Boolean(
        string='One by enrolment',
        required=False,
        readonly=False,
        index=False,
        default='Set it True to create new test for each one of the students',
        help=False
    )

    training_action_ids = fields.Many2many(
        string='Actions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        relation='academy_tests_random_template_scheduled_training_action_rel',
        column1='scheduled_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None
    )

    enrolment_ids = fields.Many2many(
        string='Enrolments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action.enrolment',
        relation='academy_tests_random_template_scheduled_enrolment_rel',
        column1='scheduled_id',
        column2='enrolment_id',
        domain=[],
        context={},
        limit=None
    )

    def _update_code(self):
        for record in self:
            pass

    @api.model
    def default_get(self, default_fields):
        """ Override parent method to append required default values

        Decorators:
            api.model

        Arguments:
            default_fields {list} -- list of field names to set default value

        Returns:
            dict -- dictionary with pairs {'field_name': value}
        """

        _super = super(AcademyTestsRandomTemplateScheduled, self)
        values = _super.default_get(default_fields)

        xid_name = 'model_academy_tests_random_template_scheduled'
        model_item = self.env.ref('academy_tests.{}'.format(xid_name))
        values['active'] = True
        values['model_id'] = model_item.id
        values['state'] = 'code'
        values['code'] = ACTION_CODE.format(-1)

        return values

    def method_direct_trigger(self):
        return self.ir_cron_id.method_direct_trigger()

    def unlink(self):
        """ Delete related cron task
        """
        _super = super(AcademyTestsRandomTemplateScheduled, self)

        ctx = {'active_test': False}
        ir_cron_ids = self.with_context(ctx).mapped('ir_cron_id')

        self._cr.autocommit(False)
        result = _super.unlink()
        ir_cron_ids.unlink()
        self._cr.commit()

        return result

    @api.model
    def create(self, values):
        """ Action code must be computed once the record has an ID
        """

        _super = super(AcademyTestsRandomTemplateScheduled, self)
        result = _super.create(values)

        # Update action code
        values = {'code': ACTION_CODE.format(self.id)}
        result.write(values)

        return result

    def write(self, values):
        """ Code must be computed by each of the records in recordset

        The action code depends on ID
        """

        if len(self) == 1:
            values['code'] = ACTION_CODE.format(self.id)
        elif 'code' in values.keys():
            values.pop('code')

        _super = super(AcademyTestsRandomTemplateScheduled, self)
        result = _super.write(values)

        if result and len(self) > 1:
            for record in self:
                values = {'code': ACTION_CODE.format(self.id)}
                record.write(values)

        return result

    # @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Prevents new record of the inherited (_inherits) model will be
        created
        """

        _super = super(AcademyTestsRandomTemplateScheduled, self)
        result = _super.copy(default)

        if result:
            for record in self:
                values = {'code': ACTION_CODE.format(self.id)}
                record.write(values)

        return result

    def _new_test(self, target_ids):
        self.ensure_one()

        for target_id in target_ids:
            self.template_id.new_test(gui=False, context_ref=target_id)

    def new_test(self):

        for record in self:

            if record.one_by_enrolment:

                path = 'training_action_ids.training_action_enrolment_ids'
                enrolment_ids = record.mapped(path)
                enrolment_ids += record.training_action_enrolment_ids

                record._new_test(enrolment_ids)

            else:

                record._new_test(record.training_action_ids)

                record._new_test(record.enrolment_ids)
