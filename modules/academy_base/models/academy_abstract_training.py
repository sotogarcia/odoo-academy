# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models

from .utils.training_mappings import MAPPING_NAME_FIELD
from .utils.training_mappings import MAPPING_WAY_DOWN
from .utils.training_mappings import MAPPING_MODEL_FIELD

from logging import getLogger


_logger = getLogger(__name__)


class AcademyAbstractTraining(models.AbstractModel):
    """Comment fields and methods will be used in all training items
    Training enrolment, action, activity, competency, module
    """

    _name = "academy.abstract.training"
    _description = "Academy abstract training"

    def get_name(self):
        self.ensure_one()

        model = self._name
        field = MAPPING_NAME_FIELD.get(model)

        return getattr(self, field)

    def get_reference(self):
        self.ensure_one()

        return "{},{}".format(self._name, self.id)

    @staticmethod
    def split_reference(reference):
        model, id_str = reference.split(",")

        return model, int(id_str)

    def get_path_down(self, stop_model=False):
        """Computes the path needed to go from one type of training to another
        type of training. Note this will return the training units as modules.

        Args:
            stop_model (bool, optional): False to go all the way

        Returns:
            str: path to go down or False if there's no way
        """

        models = list(MAPPING_WAY_DOWN.keys())

        curr_pos = models.index(self._name)
        stop_pos = models.index(stop_model) if stop_model else len(models)

        if curr_pos > stop_pos:  # There's no way down
            return False

        steps = list(MAPPING_WAY_DOWN.values())
        path = steps[curr_pos:stop_pos]

        # Patch to get all training units as modules
        if stop_model == models[-1]:
            path.append(steps[-1])

        return ".".join(path)

    def get_available(self, field="id"):
        model = self.mapped(field)._name
        model_set = self.env[model]

        for record in self:
            cursor_set = record

            if cursor_set._name == "academy.training.action.enrolment":
                if hasattr(cursor_set, field):
                    model_set += cursor_set.mapped(field)
                cursor_set = cursor_set.training_action_id

            if cursor_set._name == "academy.training.action":
                if hasattr(cursor_set, field):
                    model_set += cursor_set.mapped(field)
                cursor_set = cursor_set.training_activity_id

            if cursor_set._name == "academy.training.activity":
                if hasattr(cursor_set, field):
                    model_set += cursor_set.mapped(field)
                cursor_set = cursor_set.competency_unit_ids

            if cursor_set._name == "academy.competency.unit":
                if hasattr(cursor_set, field):
                    model_set += cursor_set.mapped(field)
                cursor_set = cursor_set.training_module_id.tree_ids

            if cursor_set._name == "academy.training.module":
                if hasattr(cursor_set, field):
                    model_set += cursor_set.mapped(field)

        return model_set

    def get_inverse_field_name(self):
        return MAPPING_MODEL_FIELD.get(self._name)
