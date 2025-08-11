# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)



class AcademyTestsTestQuestionBlockPosition(models.TransientModel):
    """
    Represents the temporary position of a block within a test 
    during the question shuffling process.
    """

    _name = 'academy.tests.test.question.block.position'
    _description = 'Temporary block/question position for shuffling wizard'

    _rec_name = 'id'
    _order = 'sequence ASC'

    wizard_id = fields.Many2one(
        string='Wizard',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Reference to the shuffle wizard this record belongs to',
        comodel_name='academy.tests.test.question.shuffle.wizard',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    block_id = fields.Many2one(
        string='Block',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='The test block whose position is being defined',
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    sequence = fields.Integer(
        string='Order',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help='Desired position of the block within the test'
    )
        
    _sql_constraints = [
        (
            'unique_wizard_block',
            'UNIQUE(wizard_id, block_id)',
            'The combination of wizard and block must be unique'
        )
    ]
