# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsQuestionRequestSetWizard(models.TransientModel):
    """ This is only a wizard to load the test related question request set or
    create new one if it doesn't exist
    """

    _name = 'academy.tests.question.request.set.wizard'
    _description = u'Academy tests question request set wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    _inherits = {'academy.tests.question.request.set': 'request_set_id'}

    request_set_id = fields.Many2one(
        string='Request set',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_request_set_id(),
        help=False,
        comodel_name='academy.tests.question.request.set',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def _default_request_set_id(self):
        request_set = self.env['academy.tests.question.request.set']

        active_model = self.env.context.get('active_model', False)
        if active_model == 'academy.tests.test':
            active_id = self.env.context.get('active_id', False)

            request_set = self._search_for_request_set(active_id)

            if not request_set:
                request_set = self._new_request_set_for_test(active_id)

        else:
            msg = _('This wizard has been implemented to be used from test')
            raise UserError(msg)

        return request_set

    def _search_for_request_set(self, test_id):
        domain = [('test_id', '=', test_id)]

        request_set = self.env['academy.tests.question.request.set']
        return request_set.search(domain, limit=1, order='create_date DESC')

    def _new_request_set_for_test(self, test_id):
        request_set = self.env['academy.tests.question.request.set']

        name = _('New request')
        name = self._read_test_name(test_id, name)

        return request_set.create({'name': name, 'test_id': test_id})

    def _read_test_name(self, test_id, default=None):
        domain = [('id', '=', test_id)]
        test_set = self.env['academy.tests.test']
        result = test_set.search_read(domain, ['name'])

        return result[0]['name'] if result else default

    @api.model
    def _context_update_test(self, result):
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)

        if active_model == 'academy.tests.test' and active_id:
            result['test_id'] = active_id

    @api.model
    def default_get(self, fields_list):
        _super = super(AcademyTestsQuestionRequestSetWizard, self)
        result = _super.default_get(fields_list)

        self._context_update_test(result)

        return result
