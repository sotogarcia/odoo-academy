# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# import logging

from odoo import models, api, fields, _

class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            followers = self.env['mail.followers'].search([
                ('res_model', '=', vals.get('res_model')),
                ('res_id', '=', vals.get('res_id')),
                ('partner_id', '=', vals.get('partner_id'))
            ])
            if len(followers):
                for p in followers:
                    p.unlink()
        return super(Followers, self).create(vals)