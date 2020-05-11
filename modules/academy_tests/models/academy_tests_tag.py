# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.tag an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the real life question difficulty tag

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestsTag(models.Model):
    """ Tag can be used to better describe this question

    Fields:
      name (Char): Human readable name which will identify each record.

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
        # oldname='academy_question_ids'
    )

    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'tag_uniq',
            'UNIQUE(name)',
            _(u'There is already another tag with the same name')
        )
    ]
