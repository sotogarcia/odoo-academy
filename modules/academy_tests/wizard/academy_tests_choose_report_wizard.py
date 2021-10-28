# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)

REPORT_TYPES = [
    ('qweb-html', 'HTML'),
    ('qweb-pdf', 'PDF'),
    ('qweb-text', 'Text'),
]


class AcademyTestChooseReportWizard(models.TransientModel):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.test.choose.report.wizard'
    _description = u'Academy test choose report wizard'

    _rec_name = 'id'
    _order = 'id ASC'

    chosen_report_id = fields.Many2one(
        string='Report',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self._default_chosen_report_id(),
        help='Choose report will be printed',
        comodel_name='ir.actions.report',
        domain=[('model', '=', 'academy.tests.test')],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    report_type = fields.Selection(
        string='Type',
        required=True,
        readonly=True,
        index=False,
        default=REPORT_TYPES[0][0],
        help='The type of the report that will be rendered',
        selection=REPORT_TYPES
    )

    report_help = fields.Text(
        string='About',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Something about chosen report',
        translate=True
    )

    target_test_ids = fields.Many2many(
        string='Taget tests',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self._default_target_tests_ids(),
        help='Choose target tests',
        comodel_name='academy.tests.test',
        relation='academy_tests_tests_choose_report_wizard_rel',
        column1='wizard_id',
        column2='tesst_id',
        domain=[],
        context={},
        limit=None
    )

    def _default_chosen_report_id(self):
        report_domain = [('model', '=', 'academy.tests.test')]
        report_obj = self.env['ir.actions.report']
        return report_obj.search(report_domain, limit=1)

    def _default_target_tests_ids(self):
        active_ids = self.env.context.get('active_ids', [])

        test_domain = [('id', 'in', active_ids)]
        test_obj = self.env['academy.tests.test']

        return test_obj.search(test_domain)

    @api.onchange('chosen_report_id')
    def _onchange_chosen_report_id(self):
        self.report_type = self.chosen_report_id.report_type
        self.report_help = self.chosen_report_id.help

    def print_report(self):
        docids = self.target_test_ids
        return self.chosen_report_id.report_action(docids)
