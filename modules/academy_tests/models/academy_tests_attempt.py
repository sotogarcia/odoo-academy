# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.addons.academy_base.models.lib.custom_model_fields import Many2manyThroughView

_logger = getLogger(__name__)


class AcademyTestsAttempt(models.Model):
    """ Logs an attempt by a user to solve a test
    """

    _name = 'academy.tests.attempt'
    _description = u'Academy tests attempt'

    _rec_name = 'id'
    _order = 'start ASC'


    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this attempt',
        translate=True
    )

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the student who performs the attempt',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose test to be attempted',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    start = fields.Datetime(
        string='Start',
        required=True,
        readonly=False,
        index=False,
        default=fields.datetime.now(),
        help='Choose date and time to start the attempt'
    )

    elapsed = fields.Float(
        string='Elapsed time',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Enter the time has been used in attempt'
    )

    available = fields.Float(
        string='Available time',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Enter the total time for the attempt'
    )


    end = fields.Datetime(
        string='End',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose date and time the attempt ended'
    )

    correction_type = fields.Selection(
        string='Correction type',
        required=True,
        readonly=False,
        index=False,
        default='test',
        help='Choose the type of attempt',
        selection=[('question', 'By question'), ('test', 'By test')]
    )

    attempt_answer_ids = fields.One2many(
        string='Answers',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Links all answer attempts',
        comodel_name='academy.tests.attempt.answer',
        inverse_name='attempt_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    attempt_final_answer_ids = Many2manyThroughView(
        string='Final answers',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.attempt.answer',
        relation='academy_tests_attempt_attempt_answer_rel',
        column1='attempt_id',
        column2='attempt_answer_id',
        domain=[],
        context={},
        limit=None
    )

    right = fields.Float(
        string='Right',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        digits=(16, 2),
        help='Score by right question'
    )

    wrong = fields.Float(
        string='Wrong',
        required=True,
        readonly=False,
        index=False,
        default=-1.0,
        digits=(16, 2),
        help='Score by wrong question'
    )

    blank = fields.Float(
        string='Blank',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Score by blank question'
    )

    lock_time = fields.Boolean(
        string='Lock time',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check to not allow the user to continue with the test once the time has passed'
    )


    _sql_constraints = [
         (
             'check_start_before_end',
             'CHECK("end" IS NULL OR start <= "end")',
             _(u'The start date/time must be anterior to the end date')
         )
     ]
