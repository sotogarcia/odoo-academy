# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingPublicAdministration(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.public.tendering.public.administration'
    _description = u'Academy public tendering administration'

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

    public_administration_type_id = fields.Many2one(
        string='Type',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose type for this administration',
        comodel_name='academy.public.tendering.public.administration.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    public_offer_ids = fields.One2many(
        string='Public offers',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose or create related public offers',
        comodel_name='academy.public.tendering.public.offer',
        inverse_name='public_administration_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    def _ensure_civil_service_category(self, values):
        cat_ops = values.get('category_id', [[6, False, []]])
        cat_xid = 'academy_public_tendering.res_partner_category_civil_service'

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

        _super = super(AcademyPublicTenderingPublicAdministration, self)
        result = _super.create(values)

        return result
