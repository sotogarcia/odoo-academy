# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceRecruitmentPublicAdministration(models.Model):
    """ Every different organization that can coordinate a selective process
    """

    _name = 'civil.service.recruitment.public.administration'
    _description = u'Civil service recruitment administration'

    _inherits = {'res.partner': 'res_partner_id'}

    _rec_name = 'name'
    _order = 'name ASC'

    res_partner_id = fields.Many2one(
        string='Partner',
        required=True,
        readonly=False,
        index=False,
        help='Choose related partner',
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    administration_type_id = fields.Many2one(
        string='Type',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose type for this administration',
        comodel_name='civil.service.recruitment.public.administration.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    offer_ids = fields.One2many(
        string='Public offers',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose or create related public offers',
        comodel_name='civil.service.recruitment.public.offer',
        inverse_name='administration_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    def _ensure_civil_service_category(self, values):
        cat_ops = values.get('category_id', [[6, False, []]])
        cat_xid = 'civil_service_recruitment.res_partner_category_civil_service'

        try:
            cat_set = self.env.ref(cat_xid)
            cat_ops[0][2].append(cat_set.id)
        except Exception as ex:
            message = ('Civil service partner category could not be assigned '
                       'to the new administration. System says: {}')
            _logger.warning(message.format(str(ex)))

    def _ensure_is_company(self, values):
        values['is_company'] = True
        values['company_type'] = 'company'

    @api.model
    def create(self, values):
        """ Ensures partner will be a company

        @note: For backward compatibility, ``values`` may be a dictionary
        """
        values = values if isinstance(values, list) else [values]

        for values_dict in values:
            self._ensure_civil_service_category(values_dict)
            self._ensure_is_company(values_dict)

        _super = super(CivilServiceRecruitmentPublicAdministration, self)
        result = _super.create(values)

        return result

    def create_company(self):
        """ This method is called by a button that exists in the Odoo 15
        partner form view, but does not exist in the analogous Odoo 13 view.

        Returns:
            dict: ir.actions.act_window
        """

        partners = self.mapped('res_partner_id')

        if partners and hasattr(partners, 'create_company'):
            method_ptr = getattr(partners, 'create_company')
            return method_ptr()