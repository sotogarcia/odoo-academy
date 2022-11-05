# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyAbstractTest(models.Model):
    """ Common test datails. This can be used by several models.
    """

    _name = 'academy.abstract.test'
    _description = u'Academy abstract test'

    kind_id = fields.Many2one(
        string='Kind',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_kind_id(),
        help='Choose the kind for this test',
        comodel_name='academy.tests.test.kind',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def default_kind_id(self):
        return self.env.ref('academy_tests.academy_tests_test_kind_common')

    repeat_images = fields.Boolean(
        string='Repeat images',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Repeat the image every time it is referred to in a question'
    )

    auto_arrange_blocks = fields.Boolean(
        string='Auto arrange blocks',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to auto arrange questions in blocks'
    )

    block_starts_page = fields.Boolean(
        string='Block starts a page',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to do each block starts a new page'
    )

    restart_numbering = fields.Boolean(
        string='Restart numbering',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to restart numbering in each block'
    )

    preamble = fields.Text(
        string='Preamble',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_preamble(),
        help='What it is said before beginning to test',
        translate=True
    )
