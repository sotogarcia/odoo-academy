# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.question.impugnment an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the real life inpugnment for a question

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
class AcademyTestsQuestionImpugnment(models.Model):
    """ Question impugnment

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.question.impugnment'
    _description = u'Academy tests, question impugnment'

    _rec_name = 'name'
    _order = 'write_date DESC, create_date DESC'

    name = fields.Char(
        string='Title',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Short impugnment description',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Long impugnment description',
        translate=True
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question related with this impugnment',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        # oldname='academy_question_id'
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
