#pylint: disable=I0011,W0212
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AptVacancyPosition(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.public.tendering.vacancy.position'
    _description = u'Public tendering, vacancy position'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Denomination',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this vacancy position',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this vacancy position',
        translate=True
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=False,
        default=1,
        help=('Order in which this vacancy position will be displayed '
              'in the tender process view')
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you '
              'to hide record without removing it.')
    )


    academy_public_tendering_vacancy_position_type_id = fields.Many2one(
        string='Vacancy position type',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.public.tendering.vacancy.position.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help=False
    )

    academy_public_tendering_process_id = fields.Many2one(
        string='Public tendering',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose academy public tendering to which this vacancy belongs',
        comodel_name='academy.public.tendering.process',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )



    def _ensure_name(self, value_dict, type_id=False):
        """ If record name field value has not been set this method gets the
        name of the vacancy type to assign it as record name
        """

        if not value_dict.get('name', False):
            type_model = 'academy.public.tendering.vacancy.position.type'
            type_obj = self.env[type_model]
            type_set = type_obj.browse(type_id)

            value_dict['name'] = type_set.name

        return value_dict


    @api.model
    def create(self, values):
        """ Touches related tendering processes to ensure state_id
        """

        # STEP 0: For backward compatibility, ``values`` may be a dictionary

        values = values if isinstance(values, list) else [values]

        # STEP 1: Use event type name as event name if it has not been set
        for value_dict in values:
            field_name = 'academy_public_tendering_vacancy_position_type_id'
            type_id = value_dict.get(field_name)
            self._ensure_name(value_dict, type_id)


        # STEP 2: Call parent create method to create record
        result = super(AptVacancyPosition, self).create(values)

        return result


    def write(self, values):
        """ Touches related tendering processes to ensure state_id
        """

        # STEP 1: Use event type name as event name if it has not been set
        type_id = self.academy_public_tendering_vacancy_position_type_id.id
        self._ensure_name(values, type_id)

        # STEP 2: Call parent create method to write record
        result = super(AptVacancyPosition, self).write(values)

        return result
