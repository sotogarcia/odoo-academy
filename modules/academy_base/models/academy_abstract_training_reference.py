# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

from .utils.training_mappings import MAPPING_MODEL_TYPE
from .utils.training_mappings import MAPPING_MODEL_FIELD
from .utils.training_mappings import MAPPING_TRAINING_TYPES
from .utils.training_mappings import MAPPING_TRAINING_REFERENCES

_logger = getLogger(__name__)


class AcademyAbstractTrainingReference(models.AbstractModel):
    """ Provides required fields and methods to make a reference for any kind
    of training items (enrolment, action, activity, competency, module)
    """

    _name = 'academy.abstract.training.reference'
    _description = u'Academy training reference'

    training_type = fields.Selection(
        string='Training type',
        required=False,
        readonly=True,
        index=False,
        default=False,
        help=False,
        selection=MAPPING_TRAINING_TYPES
    )

    training_ref = fields.Reference(
        string='Training',
        required=False,
        readonly=False,
        index=True,
        default=0,
        help='Choose training item to which the test will be assigned',
        selection=MAPPING_TRAINING_REFERENCES
    )

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The enrolment to which the test will be assigned',
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The training action to which the test will be assigned',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The training activity to which the test will be assigned',
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The competency unit to which the test will be assigned',
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_module_id = fields.Many2one(
        string='Training module',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The training module to which the test will be assigned',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('training_ref')
    def _onchange_training_ref(self):

        for record in self:

            if not record.training_ref:
                record.training_type = None
            else:
                model = record.training_ref._name
                record.training_type = self.get_training_type(model)

    _sql_constraints = [
        (
            'one_training_reference',
            '''
                CHECK(
                    training_ref IS NULL
                    OR
                    NUM_NONNULLS(
                        enrolment_id,
                        training_action_id,
                        training_activity_id,
                        competency_unit_id,
                        training_module_id
                    ) = 1
                )
            ''',
            _(u'Only one type of training item can be set by each record')
        ),
        (
            'check_training_reference',
            '''
                CHECK(
                    training_ref IS NULL
                    OR
                    SPLIT_PART(training_ref, ',', 2)::INTEGER =
                    COALESCE(
                        enrolment_id,
                        training_action_id,
                        training_activity_id,
                        competency_unit_id,
                        training_module_id
                    )
                )
            ''',
            _(u'Many2one fields must be consistent with the Reference field')
        ),
        (
            'check_training_type',
            '''
                CHECK(
                    training_ref IS NULL
                    OR
                    SPLIT_PART(training_ref, ',', 1)
                    ILIKE '%' || training_type || '%'
                )
            ''',
            _(u'Training_type must be consistent with the Reference field')
        )
    ]

    @api.model
    def create(self, values):
        """ Ensures consistency between training_ref and training_*_id fields
        """

        _super = super(AcademyAbstractTrainingReference, self)

        self._ensure_consistency_in_training(values, True)

        return _super.create(values)

    def write(self, values):
        """ Ensures consistency between training_ref and training_*_id fields
        """

        _super = super(AcademyAbstractTrainingReference, self)

        self._ensure_consistency_in_training(values, False)

        return _super.write(values)

    @api.model
    def _ensure_consistency_in_training(self, values, create=False):
        """ Ensures consistency between training_ref and training_*_id fields

        Args:
            values (dict): dictionary passed by create or update methods
            create (bool, optional): True if this method gas been called from
            the ``create`` method. This will determine whether the default
            reference will be looked up in the context.

        Returns:
            list: list [model, id_str] which allows to access this values from
            methods that override this
        """

        training_ref = values.get('training_ref', False)

        # Tries to get the default training reference from context
        if not training_ref and create:
            training_ref = self.env.context.get('default_training_ref', False)

        if training_ref:
            model, id_str = training_ref.split(',')
            values['training_type'] = self.get_training_type(model)
            self._update_training_references(values, model, int(id_str))
        else:
            model, id_str = (None, None)

        return model, id_str

    @staticmethod
    def _update_training_references(values, model, training_ref):
        target_field = MAPPING_MODEL_FIELD.get(model)

        for model, field in MAPPING_MODEL_FIELD.items():
            if field == target_field:
                values[field] = training_ref
            else:
                values[field] = None

    @staticmethod
    def get_training_type(model):
        return MAPPING_MODEL_TYPE.get(model) if model else None

    def get_training_type_name(self):
        """This method it is not used in this abstract model but it can be used
        by the models that inherit from it

        Returns:
            str: human readable name of the choose training type
        """

        self.ensure_one()

        if self.training_type:
            value = self.training_type
            match_list = [
                pair for pair in MAPPING_TRAINING_TYPES if pair[0] == value
            ]
            result = match_list[0][1] if match_list else _('Unknown')
        else:
            result = _('Not established')

        return result
