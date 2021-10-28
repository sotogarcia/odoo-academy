# -*- coding: utf-8 -*-
""" AcademyTestsQuestionType

This module contains the academy.tests.question.type Odoo model which stores
all academy tests question type attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsQuestionType(models.Model):
    """ This is a property of the academy.tests.question model
    """

    _name = 'academy.tests.question.type'
    _description = u'Academy tests, question type'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
        translate=True,
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )
