# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTestQuestionRel(models.Model):
    """
    """

    _inherit = 'academy.tests.test.question.rel'

    def _gift_title(self, new_line=True):
        """ Build a valid gift title using record ID
        // https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained
        """
        pattern = '::SEQ-{:04}::{}'
        return pattern.format(self.sequence, '\n' if new_line else '')

    def to_gift(self):
        self.ensure_one()

        title = self._gift_title()

        return self.question_id.to_gift(title=title)
