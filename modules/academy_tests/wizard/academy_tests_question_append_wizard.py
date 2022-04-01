# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Question Append

This module contains the academy.tests.question.append wizard which allows
to append some question to one or more tests

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields
from odoo.tools.translate import _

from odoo.exceptions import ValidationError, UserError

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class Nameofmodel(models.TransientModel):
    """ This model is the representation of the name of model
    """

    _name = 'academy.tests.question.append.wizard'
    _description = u'Academy tests, question append wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_test_id(),
        help='Test to which questions will be append',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_link_ids = fields.One2many(
        string='Questions',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_question_ids(),
        help=False,
        comodel_name='academy.tests.question.append.wizard.link',
        inverse_name='wizard_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    def _get_active_ids(self):
        """Get active_ids context keyword values

        Returns:
            list: list of integers with gotten IDs
        """
        return self.env.context.get('active_ids', [])

    def _get_active_model_and_path(self):
        """ Get active_model from context and choose mapping path to access to
        question ID
        """
        model = self.env.context.get('active_model')

        if model == 'academy.tests.test.question.rel':
            return model, 'question_id.id'
        elif model == 'academy.tests.question':
            return model, 'id'

        return False, False

    def default_question_ids(self):
        """ Get default `id` values from context, these will be questions
        had been chosen before launch this wizard
        """

        x2mop = [(5, 0, 0)]

        active_ids = self._get_active_ids()
        active_model, path_for_id = self._get_active_model_and_path()

        if active_model and active_ids:

            domain = [('id', 'in', active_ids)]
            model_obj = self.env[active_model]
            record_set = model_obj.search(domain)

            sequence = 0
            for record in record_set:
                sequence += 1
                values = {
                    'wizard_id': self.id,
                    'question_id': record.mapped(path_for_id)[0],
                    'sequence': sequence
                }
                x2mop.append((0, 0, values))

        return x2mop

    def default_test_id(self):
        """ Get last test used with wizard. Wizard is a transient model
        therefore there could be none.
        """

        uid = self.env.context.get('uid', -1)
        domain = [('create_uid', '=', uid)]
        order = 'write_date desc, create_date desc, id desc'

        wizard_set = self.search(domain, limit=1, order=order)

        if wizard_set and wizard_set.test_id:
            return wizard_set.test_id.id

        test_obj = self.env['academy.tests.test']
        test_set = test_obj.search(domain, limit=1, order=order)

        return test_set.id if test_set else False

    def _ensure_required(self):
        # pylint: disable=locally-disabled, W0101
        if not self.test_id:
            raise ValidationError(_('Test field is required'))
            return False

        if not self.question_link_ids:
            raise ValidationError(_('Questions field is required'))
            return False

        return True

    def _get_last_sequence(self):
        rel_domain = [('test_id', '=', self.test_id.id)]
        rel_obj = self.env['academy.tests.test.question.rel']
        rel_set = rel_obj.search(rel_domain, limit=1, order='sequence desc')

        return rel_set.sequence if rel_set else 0

    def execute(self):
        """ Performs the wizard action
        """
        dep_msg = _('Question with dependencies must be added manually')
        self.ensure_one()
        self._ensure_required()

        sequence = self._get_last_sequence()

        operations = []
        for link in self.question_link_ids:
            if link.question_id.depends_on_id:
                raise UserError(dep_msg)

            sequence += 1
            link = {'sequence': sequence, 'question_id': link.question_id.id}
            operations.append((0, None, link))

        if self.test_id and operations:
            self.test_id.question_ids = operations

        self.test_id.resequence()
