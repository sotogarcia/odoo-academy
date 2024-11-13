# -*- coding: utf-8 -*-
""" AcademyTestsTag

This module contains the academy.tests.tag Odoo model which stores
all academy tests tag attributes and behavior.
"""

from odoo import models, fields
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTag(models.Model):
    """ This is a property of the academy.tests.test model
    """

    _name = 'academy.tests.tag'
    _description = u'Academy tests, question tag'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this tag',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this question',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it')
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Questions relating to this tag',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_tag_rel',
        column1='tag_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
    )

    private = fields.Boolean(
        string='Private',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Checked to restrict the visibility of the tag to the creator '
              'only')
    )

    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'tag_uniq',
            'UNIQUE(name)',
            _(u'There is already another tag with the same name')
        )
    ]

    def name_get(self):
        result = []
        current_user = self.env.user

        for record in self:
            name = record.name or _('New tag')

            if record.private and record.create_uid != current_user:
                creator = record.create_uid.name or _('Anonymous')
                name = '{}: {}'.format(creator, name)

            result.append((record.id, name))

        return result
