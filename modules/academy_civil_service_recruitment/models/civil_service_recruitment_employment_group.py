# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceRecruitmentEmploymentGroup(models.Model):
    """ Group of public administration corps that require a similar degree
    """

    _inherit = ['civil.service.recruitment.employment.group']

    qualification_level_id = fields.Many2one(
        string='Qualification level',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_qualification_level(),
        help='Choose minimun required qualification level',
        comodel_name='academy.qualification.level',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def default_qualification_level(self):
        module = 'academy_base'
        name = 'academy_qualification_level_level_isced_2011_2'

        imd_domain = [('module', '=', module), ('name', '=', name)]
        imd_obj = self.env['ir.model.data']
        imd_set = imd_obj.search(imd_domain)

        return imd_set.res_id if imd_set else None
