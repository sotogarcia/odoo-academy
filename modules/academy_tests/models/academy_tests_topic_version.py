# -*- coding: utf-8 -*-
""" AcademyTestsTopicVersion

This module contains the academy.tests.topic.version Odoo model which stores
all academy tests topic version attributes and behavior.
"""

from odoo import models, fields
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsTopicVersion(models.Model):
    """ A topic can have more than one versions, this model represents these
    versions.
    """

    _name = 'academy.tests.topic.version'
    _description = u'Academy tests topic version'

    _rec_name = 'name'
    _order = 'sequence DESC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this version',
        size=1024,
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this version or uncheck to archivate'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this version',
        translate=True
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help=('Place of this version in the order of the versions from parent')
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the parent topic',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    _sql_constraints = [
        (
            'unique_version_by_topic',
            'UNIQUE("name", "topic_id")',
            _('There is already another version with the first name')
        )
    ]

