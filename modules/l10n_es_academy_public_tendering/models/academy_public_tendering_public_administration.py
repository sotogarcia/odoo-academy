# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################


from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AcademyPublicTenderingPublicAdministration(models.Model):
    """  academy.public.tendering.public.administration model inheritance to
    add autonomous community non mandatory field
    """

    _name = 'academy.public.tendering.public.administration'
    _inherit = ['academy.public.tendering.public.administration']

    autonomy_id = fields.Many2one(
        string='Autonomy',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the related autonomy',
        comodel_name='academy.public.tendering.autonomous.community',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('state_id')
    def _onchange_state_id(self):
        """ When exists an autonomous community related with chosen state_id
        it will be automatically set
        """

        for record in self:
            record.autonomy_id = self.state_id.autonomy_id

    def _get_autonomic_type(self):
        """ First check if exists an external ID for the target type, later
        check if exists in the database and finally reads it
        """

        model = 'academy.public.tendering.public.administration.type'
        name = 'academy_public_tendering_public_administration_type_autonomic'
        md_domain = [
            ('module', '=', 'l10n_es_academy_public_tendering'),
            ('model', '=', model),
            ('name', '=', name),
        ]
        md_obj = self.env['ir.model.data']
        md_set = md_obj.search(md_domain)

        if md_set:
            rpc_obj = self.env[model]
            return rpc_obj.browse(md_set.res_id)

        return None

    @api.constrains('public_administration_type_id')
    def _check_autonomy_id(self):
        """ If administration type is autonomic and autonomy have not been
        set, a valdiation error will be raised
        """

        atype = self._get_autonomic_type()
        message = 'Administration type «{}» requires an autonomous community'

        if atype:
            aid = atype.id
            message = message.format(atype.name)
            for record in self:
                _id = record.public_administration_type_id.id
                if _id == aid and not record.autonomy_id:
                    raise ValidationError(message)
