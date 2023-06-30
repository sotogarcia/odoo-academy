# -*- coding: utf-8 -*-
""" AcademyTestsQuestionImpugnmentReply

This module contains the academy.tests.question.impugnment.reply Odoo model
which stores all teacher replies for student impugnments, as well as their
attributes and behavior.
"""

from logging import getLogger

from odoo import models, fields, api

_logger = getLogger(__name__)


class AcademyTestsQuestionImpugnmentReply(models.Model):
    """ Reply to an existin question impugnment
    """

    _name = 'academy.tests.question.impugnment.reply'
    _description = u'Academy tests question impugnment reply'

    _rec_name = 'id'
    _order = 'write_date ASC, create_date ASC'

    description = fields.Text(
        string='Description',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Long impugnment description',
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

    impugnment_id = fields.Many2one(
        string='Impugnment',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose related impugnment',
        comodel_name='academy.tests.question.impugnment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
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

    html = fields.Html(
        string='Html',
        related='impugnment_id.html',
        readonly=True
    )

    markdown = fields.Text(
        string='Markdown',
        related='impugnment_id.markdown',
        readonly=True
    )

    last_reply = fields.Text(
        string='Last reply',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Texto of the last reply or impugnment',
        translate=True,
        compute='_compute_last_reply'
    )

    state = fields.Selection(
        string='State',
        required=True,
        readonly=False,
        index=False,
        default='reply',
        help='Wizard status bar progress',
        selection=[
            ('reply', 'Reply'),
            ('options', 'Options')
        ]
    )

    @api.depends('impugnment_id')
    def _compute_last_reply(self):
        for record in self:
            reply_set = record.mapped('impugnment_id.reply_ids').filtered(
                lambda x: bool(x.description))

            if record.create_date:
                reply_set = reply_set.filtered(
                    lambda x: x.create_date < record.create_date)

            if reply_set:
                record.last_reply = reply_set[-1].description
            else:
                record.last_reply = record.impugnment_id.description

    def create(self, values):
        """ Call parent inpugnment update method
        """

        _super = super(AcademyTestsQuestionImpugnmentReply, self)
        result = _super.create(values)

        result.impugnment_id.update_state()

        return result

    def write(self, values):
        """ Call parent inpugnment update method
        """

        _super = super(AcademyTestsQuestionImpugnmentReply, self)
        result = _super.write(values)

        self.impugnment_id.update_state()

        return result
