# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Random Wizard Set

This module contains the academy.tests.random.wizard.Set an unique Odoo model
which contains all Academy Tests Random Wizard Set attributes and behavior.

This model is the representation of the real life academy tests random template

Classes:
    AcademyTestsRandomWizardSet: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

    Inside this class can be, in order, the following attributes and methods:
    * Object attributes like name, description, inheritance, etc.
    * Entity fields with the full definition
    * Computed fields and required computation methods
    * Events (@api.onchange) and other field required methods like computed
    domain, defaul values, etc...
    * Overloaded object methods, like create, write, copy, etc.
    * Public object methods will be called from outside
    * Private auxiliary methods not related with the model fields, they will
    be called from other class methods


Todo:
    * Complete the model attributes and behavior

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestsRandomWizardSet(models.Model):
    """ This model is the representation of the academy tests random template

    Fields:
      name (Char)       : Human readable name which will identify each record
      description (Text): Something about the record or other information which
      has not an specific defined field to store it.
      active (Boolean)  : Checked do the record will be found by search and
      browse model methods, unchecked hides the record.

    """


    _name = 'academy.tests.random.template'
    _description = u'Academy Tests Random Wizard Set'

    _inherit = ['image.mixin', 'mail.thread']
    
    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=50,
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

    random_line_ids = fields.One2many(
        string='Random lines',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.random.line',
        inverse_name='random_wizard_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    test_ids = fields.One2many(
        string='Used in',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        inverse_name='random_wizard_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    # -------------------------------- CRUD -----------------------------------

    @api.model
    def create(self, values):
        """ Create a new record for a model AcademyTestsRandomWizardSet
            @param values: provides a data for new record

            @return: returns a id of new record
        """

        result = super(AcademyTestsRandomWizardSet, self).create(values)

        return result

    # @api.multi
    def write(self, values):
        """ Update all record(s) in recordset, with new value comes as {values}
            @param values: dict of new values to be set

            @return: True on success, False otherwise
        """

        result = super(AcademyTestsRandomWizardSet, self).write(values)

        return result
