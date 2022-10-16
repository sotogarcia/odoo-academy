# -*- coding: utf-8 -*-
""" ResUsers

This module extend res.users model to link to own training resources
"""

from odoo import models, fields
from odoo.tools.translate import _


from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class ResUsers(models.Model):
    """ This model extends bae.model_res_users
    """

    _name = 'res.users'
    _inherit = ['res.users']

    training_resource_ids = fields.One2many(
        string='Training resources',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the training resources which he/she must update',
        comodel_name='academy.training.resource',
        inverse_name='updater_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    def convert_to_teacher(self):
        """ Convert user in teacher
        """

        teacher_obj = self.env['academy.teacher']
        teacher = None

        teacher_group_xid = 'academy_base.academy_group_teacher'
        teacher_group = self.env.ref(teacher_group_xid)

        for record in self:
            domain = [('res_users_id', '=', record.id)]
            teacher = teacher_obj.search(domain, limit=1)

            if teacher:
                msg = _('Teacher {} already exists for user {}.')
                _logger.warning(msg.format(teacher.id, record.id))

            else:
                values = {'res_users_id': record.id}
                teacher = teacher_obj.create(values)

                msg = _('New teacher {} created for user {}.')
                _logger.info(msg.format(teacher.id, record.id))

            if not record.has_group(teacher_group_xid):
                record.groups_id = [(4, teacher_group.id, None)]

        if teacher:
            action = {
                'name': _('Created teachers'),
                'type': 'ir.actions.act_window',
                'view_mode': 'kanban,tree,form',
                'view_type': 'form',
                'view_id': False,
                'res_model': 'academy.teacher',
                'res_id': None,
                'nodestroy': True,
                'target': 'current',
                'domain': [('res_users_id', 'in', self.mapped('id'))],
            }

            if len(self) == 1:
                action['res_id'] = teacher.id,

            return action
