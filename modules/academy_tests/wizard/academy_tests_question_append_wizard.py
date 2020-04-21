# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Question Append

This module contains the academy.tests.question.append wizard which allows
to append some question to one or more tests

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


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

    question_ids = fields.Many2many(
        string='Questions',
        required=True,
        readonly=False,
        index=False,
        help='False',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_append_wizard_rel',
        column1='question_append_wizard_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        default=lambda self: self.default_question_ids(),
    )


    def default_question_ids(self):
        """ Get default `id` values from context, these will be questions
        had been choosen before launch this wizard
        """
        ids = self.env.context.get('active_ids', [])
        return [(6, None, ids)] if ids else False


    def default_test_id(self):
        """ Get last test used with wizard. Wizard is a transient model
        therefore there could be none.
        """

        uid = self.env.context.get('uid', -1)
        domain = ['|', ('create_uid', '=', uid), ('write_uid', '=', uid)]
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

        if not self.question_ids:
            raise ValidationError(_('Questions field is required'))
            return False

        return True


    def _get_last_sequence(self):
        rel_domain = [('test_id', '=', self.test_id.id)]
        rel_obj = self.env['academy.tests.test.question.rel']
        rel_set = rel_obj.search(rel_domain, limit=1, order='sequence desc')

        return rel_set.sequence if rel_set else 0


    # @api.multi
    def execute(self):
        """ Performs the wizard action
        """
        self.ensure_one()
        self._ensure_required()

        sequence = self._get_last_sequence()
        rel_obj = self.env['academy.tests.test.question.rel']

        for question_id in self.question_ids:
            values = {
                'test_id': self.test_id.id,
                'question_id': question_id.id,
                'sequence': sequence + 1,
                'active': question_id.active and self.test_id.active
            }

            rel_obj.create(values)






