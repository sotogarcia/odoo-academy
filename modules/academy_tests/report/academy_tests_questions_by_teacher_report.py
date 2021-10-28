# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


ACTION_NAME = ('academy_tests.'
               'action_report_academy_tests_questions_by_teacher')
MODEL_NAME = ('report.academy_tests.'
              'view_academy_tests_questions_by_teacher_report_qweb')


class AcademyTestsQuestionsByTeacherReport(models.AbstractModel):
    """ Questions by teacher
    """

    _name = MODEL_NAME

    _description = 'Report to print tests'

    _report_xid = ACTION_NAME
    _target_model = 'academy.teacher'

    @api.model
    def _get_report_values(self, docids, data=None):

        teacher_domain = [('id', 'in', docids)]
        teacher_obj = self.env[self._target_model]
        teacher_set = teacher_obj.search(teacher_domain)

        docargs = {
            'doc_ids': docids,
            'doc_model': self.env['academy.teacher'],
            'data': data,
            'docs': teacher_set,
        }

        return docargs
