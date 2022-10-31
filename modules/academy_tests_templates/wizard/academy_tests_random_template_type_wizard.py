# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

from odoo.addons.academy_base.models.academy_abstract_training_reference \
    import MAPPING_TRAINING_REFERENCES

_logger = getLogger(__name__)


class AcademyTestsRandomTemplateTypeWizard(models.TransientModel):
    """ Allow user to choose the type of template will be created
    """

    _name = 'academy.tests.random.template.type.wizard'
    _description = u'Academy tests random template type wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    kind = fields.Selection(
        string='Type of template',
        required=True,
        readonly=False,
        index=True,
        default='basic',
        help=_('Choose Basic to create one line by each competency/module or '
               'Extended to create one line by each module-topic link'),
        selection=[
            ('basic', 'Basic'),
            ('extended', 'Extended')]
    )

    training_ref = fields.Reference(
        string='Training',
        required=False,
        readonly=False,
        index=True,
        default=lambda self: self._default_training_ref(),
        help='Choose training item to which the test will be assigned',
        selection=MAPPING_TRAINING_REFERENCES
    )

    supplementary = fields.Integer(
        string='Supplementary',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Append supplementary questions'
    )

    block_id = fields.Many2one(
        string='Block',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_block_id(),
        help='Choose a test block to group the supplementary questions',
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def default_block_id(self):
        xid = 'academy_tests.academy_tests_test_block_supplementary'
        return self.env.ref(xid).id

    def _default_training_ref(self):
        return self.env.context.get('training_ref', False)

    def new_template(self):
        self.ensure_one()

        training_ref = self.training_ref.get_reference()

        context = self.env.context.copy()
        block_id = self.block_id.id if self.block_id else None
        context.update({
            'supplementary_quantity': self.supplementary,
            'supplementary_block_id': block_id
        })

        template_obj = self.env['academy.tests.random.template']
        template_obj = template_obj.with_context(context)
        result = template_obj.template_for_training(
            training_ref, (self.kind == 'extended'))

        return result
