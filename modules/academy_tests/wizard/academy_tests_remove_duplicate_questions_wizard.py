# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsRemoveDuplicateQuestionsWizard(models.TransientModel):
    """ Allow to remove question duplicates

    """

    _name = 'academy.tests.remove.duplicate.questions.wizard'
    _description = u'Academy tests remove duplicate questions wizard'

    _rec_name = 'id'
    _order = 'id ASC'

    question_id = fields.Many2one(
        string='Original',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    html = fields.Html(
        string='Html',
        related="question_id.html"
    )

    duplicated_ids = fields.Many2many(
        string='Duplicated',
        related="question_id.duplicated_ids"
    )

    @api.model
    def _get_original_questions(self, question_set):
        target_set = self.env['academy.tests.question']

        for question_item in question_set:
            if question_item.original_ids:
                target_set += question_item.original_ids
            else:
                target_set += question_item

        return target_set

    @api.model
    def _search_links(self, question_item):

        link_obj = self.env['academy.tests.test.question.rel']

        duplicate_ids = question_item.duplicated_ids.mapped('id')
        domain = [('question_id', 'in', duplicate_ids)]
        link_set = link_obj.search(domain, order='id asc')

        return link_set

    def _new_link_already_exists(self, link_item, question_item):
        domain = [
            ('test_id', '=', link_item.test_id.id),
            ('question_id', '=', question_item.id)
        ]
        link_set = self.env['academy.tests.test.question.rel']

        return bool(link_set.search(domain))

    @api.model
    def _update_links(self, question_item):
        link_set = self._search_links(question_item)

        for link_item in link_set:
            if self._new_link_already_exists(link_item, question_item):
                link_item.unlink()
            else:
                link_item.write({'question_id': question_item.id})

    @api.model
    def _remove_duplicates(self, question_item):
        question_item.duplicated_ids.unlink()

    @api.model
    def remove_duplicates(self, question_set):

        target_set = self._get_original_questions(question_set)

        self._cr.autocommit(False)

        for question_item in target_set:
            try:
                self._update_links(question_item)
                self._remove_duplicates(question_item)

                self._cr.commit()

            except Exception as ex:
                self._cr.rollback()

                raise UserError(ex)

        self._cr.autocommit(True)

    def amend(self):
        self.ensure_one()
        self.remove_duplicates(self.question_id)


"""
-- Active first
select coalesce(v, False) as f from (values (true), (false), (null)) as t(v) order by f desc
"""

"""

END;
BEGIN;
WITH computed AS (
    SELECT
        links."id",
        links.test_id,
        dups.question_id AS original_id,
        duplicate_id,
        COUNT (*) OVER ( PARTITION BY test_id, dups.question_id ORDER BY test_id, dups.question_id, links.create_date ASC ) :: INTEGER AS possibilities
    FROM
        academy_tests_test_question_rel AS links
        INNER JOIN academy_tests_question_duplicated_rel AS dups ON links.question_id = dups.duplicate_id
    ) UPDATE academy_tests_test_question_rel AS rel1
    SET question_id = original_id
FROM
    computed AS cmp
WHERE
    possibilities = 1
    AND question_id = duplicate_id
    AND rel1.test_id = cmp.test_id
    AND NOT EXISTS ( SELECT 1 FROM academy_tests_test_question_rel AS rel2 WHERE rel2.test_id = rel1.test_id AND rel2.question_id = original_id )
    AND rel1.question_id IN (SELECT "id" FROM academy_tests_question AS atq WHERE owner_id = 13);
ROLLBACK;

"""