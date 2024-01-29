# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

# NOTE: Some fields use ``compute_sudo=True`` to prevent an extrange warning
# from using the same method to calculate stored and non-stored fields. See:
# https://github.com/odoo/odoo/issues/39306

from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingAction(models.Model):
    """
    """

    _name = 'academy.training.action'

    _inherit = ['academy.training.action']

    facility_link_ids = fields.One2many(
        string='Facility links',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Required educational facilities in relevance order',
        comodel_name='academy.training.action.facility.link',
        inverse_name='training_action_id',
        domain=[('competency_unit_id', '=', False)],
        context={},
        auto_join=False,
        limit=None
    )

    facility_ids = fields.Many2manyView(
        string='Facilities',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Required educational facilities',
        comodel_name='facility.facility',
        relation='academy_training_action_facility_link',
        column1='training_action_id',
        column2='facility_id',
        domain=[],
        context={},
        limit=None
    )

    primary_facility_id = fields.Many2one(
        string='Primary facility',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Main educational facility',
        comodel_name='facility.facility',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False,
        compute='_compute_fields_dependent_on_facility_link_ids',
        search='_search_primary_facility_id',
        compute_sudo=True  # See this module comments and the top of the file
    )

    @api.model
    def _search_primary_facility_id(self, operator, value):
        if value is True and operator == '=':
            result = self._search_primary([0], 'facility_id', denial=True)
        elif value is True and operator in ('!=', '<>'):
            result = self._search_primary([0], 'facility_id', denial=False)
        elif value is False and operator == '=':
            result = self._search_primary([0], 'facility_id', denial=False)
        elif value is False and operator in ('!=', '<>'):
            result = self._search_primary([0], 'facility_id', denial=True)
        else:
            complex_obj = self.env['facility.complex']
            complex_set = complex_obj.name_search(
                name=value, operator=operator, limit=None)
            result = self._search_primary(complex_set, 'facility_id')

        return result

    primary_complex_id = fields.Many2one(
        string='Primary complex',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Main educational complex',
        comodel_name='facility.complex',
        domain=[],
        context={},
        ondelete='restrict',
        auto_join=False,
        compute='_compute_fields_dependent_on_facility_link_ids',
        search='_search_primary_complex_id',
        store=True,
        compute_sudo=True  # See this module comments and the top of the file
    )

    @api.depends('facility_link_ids')
    def _compute_fields_dependent_on_facility_link_ids(self):
        for record in self:
            link_set = record.facility_link_ids.sorted(lambda r: r.sequence)
            if not link_set:
                record.primary_complex_id = None
                record.primary_facility_id = None
            else:
                record.primary_complex_id = link_set[0].facility_id.complex_id
                record.primary_facility_id = link_set[0].facility_id._origin.id

            record.facility_count = len(link_set)

    @api.model
    def _search_primary_complex_id(self, operator, value):
        if value is True and operator == '=':
            result = self._search_primary([0], 'complex_id', denial=True)
        elif value is True and operator in ('!=', '<>'):
            result = self._search_primary([0], 'complex_id', denial=False)
        elif value is False and operator == '=':
            result = self._search_primary([0], 'complex_id', denial=False)
        elif value is False and operator in ('!=', '<>'):
            result = self._search_primary([0], 'complex_id', denial=True)
        else:
            complex_obj = self.env['facility.complex']
            complex_set = complex_obj.name_search(
                name=value, operator=operator, limit=None)
            result = self._search_primary(complex_set, 'complex_id')

        return result

    def _search_primary(self, target_set, target_field, denial=False):
        """ Search for training actions where primary complex ID or primary
        facility ID matches with any of the given set of IDs.

        To find training actions with no complex or with no facility you can
        provide a set formed only by the ID zero (0).

        Args:
            target_set (tuple): tuple of IDs. Use a set formed only by the ID
            zero (0) to search training actions with no complex or facility.
            target_field (str): name of the field will be used in where clause;
            use complex_id to search by complex or facility_id to search by
            facility.
            denial (bool, optional): if will be set to False the ``IN`` SQL
            logical opearator will be used, otherwise the ``NOT IN`` SQL
            logical operator will be used insted.

        Returns:
            list: Odoo valid domain using training action ID field and the
            expected values.
        """

        sql = '''
            SELECT DISTINCT ON
                ( ata."id" ) ata."id" AS training_action_id,
                COALESCE ( ff."id", 0 ) :: INTEGER AS facility_id,
                COALESCE ( ff.complex_id, 0 ) :: INTEGER AS complex_id
            FROM
                academy_training_action AS ata
            LEFT JOIN academy_training_action_facility_link AS link
                ON link.training_action_id = ata."id"
            LEFT JOIN facility_facility AS ff ON ff."id" = link.facility_id
            WHERE
                {target} {op} ({ids})
            ORDER BY
                ata."id",
                link."sequence" ASC NULLS LAST,
                facility_id DESC NULLS LAST;
        '''

        domain = FALSE_DOMAIN
        op = 'NOT IN' if denial else 'IN'

        if target_set:
            target_ids = [item[0] for item in target_set]
            target_ids = ', '.join([str(item) for item in target_ids])
            sql = sql.format(target=target_field, op=op, ids=target_ids)

            self.env.cr.execute(sql)
            rows = self.env.cr.dictfetchall()
            if rows:
                ids = [row['training_action_id'] for row in (rows or [])]
                domain = [('id', 'in', ids)]

        return domain

    facility_count = fields.Integer(
        string='Facility count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=('Number of educational facilities will be required to teach the '
              'training action'),
        compute='_compute_fields_dependent_on_facility_link_ids',
        search='_search_facility_count',
        compute_sudo=True  # See this module comments and the top of the file
    )

    @api.model
    def _search_facility_count(self, operator, value):
        sql = '''
            SELECT
                ata."id"
            FROM
                academy_training_action AS ata
            LEFT JOIN academy_training_action_facility_link AS link
                ON link.training_action_id = ata."id"
            GROUP BY ata."id"
            HAVING COUNT(link.training_action_id) {operator} {value}
        '''

        if value is True:
            domain = TRUE_DOMAIN if operator == '=' else FALSE_DOMAIN

        elif value is False:
            domain = TRUE_DOMAIN if operator == '!=' else FALSE_DOMAIN

        else:
            domain = FALSE_DOMAIN

            sql = sql.format(operator=operator, value=value)
            self.env.cr.execute(sql)
            rows = self.env.cr.dictfetchall()
            if rows:
                action_ids = [row['id'] for row in (rows or [])]
                domain = [('id', 'in', action_ids)]

        return domain
