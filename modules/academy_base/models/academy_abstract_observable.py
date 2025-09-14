# -*- coding: utf-8 -*-
""" AcademyObservableModel

===================================================
= This will be the Observable in Observer Pattern =
====================================================

This module contains an abstract model with the necessary behavior to
perform some database record updates between related models.

The Obserser model must have a method with this signature:
```
    # pylint: disable=locally-disabled, W0613
    def update_from_external(self, crud, fieldname, recordset):
```

"""

import types

from logging import getLogger
from odoo import models, fields, api

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903,W0212
class AcademyObservableModel(models.AbstractModel):
    """Models can extend this to touch related models through 'x2many' fields"""

    _name = "academy.abstract.observable"
    _description = "Academy observer pattern: observable class"

    # -------------------------- AUXILIARY METHODS ----------------------------

    @staticmethod
    def _is_relational(field):
        """Check if given field is a relational field"""

        relational = (fields.Many2one, fields.One2many, fields.Many2many)
        return isinstance(field, relational)

    @staticmethod
    def _is_not_magic(field):
        """Check if given field is a Odoo special field"""

        return field.name not in models.MAGIC_COLUMNS

    def _is_observer(self, field):
        """Check if given field is related with a model which has a method
        named ``update_from_external``, this method will be called when this
        model record changes
        """

        mname = "update_from_external"
        comodel = self.env[field.comodel_name]

        if hasattr(comodel, mname):
            method = getattr(comodel, mname)
            return isinstance(method, types.MethodType)

        return False

    def _get_observers(self):
        """Walk over relational fields checking if comodel has update method"""

        result = []

        for name, field in self._fields.items():
            if (
                self._is_relational(field)
                and self._is_not_magic(field)
                and self._is_observer(field)
            ):
                result.append(name)

        return result

    def _get_state(self, observers):
        """Returns a dictionary {field name: field value} with all fields
        in ONE RECORD of this model which must be updated
        """

        result = {}

        self.ensure_one()

        for fname in observers:
            value = getattr(self, fname)
            result.update({fname: value})

        return result

    def _get_states(self):
        """Returns a list of dictionaries {field name: field value} with all
        fields in each one of records of this model which must be updated
        """

        observers = self._get_observers()
        result = []

        for record in self:
            # pylint: disable=locally-disabled, W0212
            result.append(record._get_state(observers))

        return result

    def _notify(self, crud, targets):
        for target in targets:
            for fieldname, recordset in target.items():
                method = getattr(recordset, "update_from_external")
                method(crud, fieldname, self)

    # -------------------------- OVERLOADED METHODS ---------------------------

    @api.model_create_multi
    def create(self, value_list):
        """Overridden method 'create'"""

        result = super(AcademyObservableModel, self).create(value_list)
        newstates = result._get_states()

        # Send notice to the observers
        self._notify("write", newstates)

        return result

    def write(self, values):
        """Call update method in observers"""

        oldstates = self._get_states()
        result = super(AcademyObservableModel, self).write(values)
        newstates = self._get_states()

        # Send notice to the observers
        self._notify("write", oldstates)
        self._notify("write", newstates)

        return result

    def unlink(self):
        """Call update method in observers"""

        oldstates = self._get_states()
        result = super(AcademyObservableModel, self).unlink()

        # Send notice to the observers
        self._notify("write", oldstates)

        return result
