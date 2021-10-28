# -*- coding: utf-8 -*-
""" AcademyTestsQuestionImpugnment

This module contains the academy.tests.question.impugnment Odoo model which
stores all student impugnments for questions, their attributes and behavior.
"""

from logging import getLogger

from odoo import models, fields, api

_logger = getLogger(__name__)


class AcademyTestsQuestionImpugnment(models.Model):
    """ Studens can impugn questions, this model stores the impugnment details
    """

    _name = 'academy.tests.question.impugnment'
    _description = u'Academy tests, question impugnment'

    _inherit = ['academy.abstract.owner', 'mail.thread']

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

    student_id = fields.Many2one(
        string='Student',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose student who impugn this question',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    parent_id = fields.Many2one(
        string='Parent impugnment',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose parent impugnment',
        comodel_name='academy.tests.question.impugnment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    reply_ids = fields.One2many(
        string='Replies',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question.impugnment.reply',
        inverse_name='impugnment_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

