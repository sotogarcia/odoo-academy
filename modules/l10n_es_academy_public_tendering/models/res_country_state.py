# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################


from odoo import models, fields


class ResCountryState(models.Model):
    """ res.country.state model inheritance to add autonomous community non
    mandatory field
    """

    _name = 'res.country.state'
    _inherit = ['res.country.state']

    autonomy_id = fields.Many2one(
        string='Autonomy',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose autonomous community to which this state belongs',
        comodel_name='academy.public.tendering.autonomous.community',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
