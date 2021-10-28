# -*- coding: utf-8 -*-
""" AcademyTrainingResourceFile

This module contains the academy.action.resource.file Odoo model which stores
all training resource file attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingResourceFile(models.Model):
    """ When a training resource has been linked to local directory, this
    folder will have several files. This model will be used to store the
    information of these files.
    """

    _name = 'academy.training.resource.file'
    _description = u'Academy training resource file'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=256,
        translate=True
    )

    training_resource_id = fields.Many2one(
        string='Training resource',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
