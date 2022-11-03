# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" SQL

This module contains the sql used in some custom views
"""


def is_numeric(operand):
    """ Check if given value is a number value or number saved as text

    Arguments:
        operand mixed -- value will be checked

    Returns:
        bool -- True if given value looks like a number, False otherwise
    """

    return isinstance(operand, int) or \
        (isinstance(operand, int) and operand.isnumeric())


def fix_established(operator, operand):
    """ Fix the given operator and operand to adapt them to be used in
    an SQL clause to search records to search records in which the value
    has been set or unset.

    This only applies when the operand is True or False.

    Arguments:
        operator str -- one of the odoo.osv.expresion.TERM_OPERATORS values
        operand mixed -- any value. Only True, False or None have effect

    Returns:
        tuple -- (operator, operand) both fixed, operator and operand
    """

    if not is_numeric(operand):
        operand = 0

        if operand is True:
            operator == '>=' if operator == '=' else '='
        elif operand is False or operand is None:
            operator == '>=' if operator == '!=' else '='

    return operator, operand
