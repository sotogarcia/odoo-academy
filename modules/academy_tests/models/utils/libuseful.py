# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" SQL

This module contains the sql used in some custom views
"""

from os import linesep
from odoo.exceptions import UserError
from odoo.tools.translate import _

# -------------------------- AUXILIARY METHODS ----------------------------


def eval_domain(domain):
    """ Evaluate a domain expresion (str, False, None, list or tuple) an
    returns a valid domain

    Arguments:
        domain {mixed} -- domain expresion

    Returns:
        mixed -- Odoo valid domain. This will be a tuple or list
    """

    if domain in [False, None]:
        domain = []
    elif not isinstance(domain, (list, tuple)):
        try:
            domain = eval(domain)
        except Exception:
            domain = []

    return domain


def prepare_text(text, line_prefix=None):
    """ This method strips each line in the given text and it attach
    to each one a prefix if applicable

    @param text (str): to split
    @param line_prefix (str): prefix will be added to each line

    @return (str): multiple line string
    """

    lines = text.splitlines()
    line_prefix = line_prefix + ' ' if line_prefix else ''

    for index in range(0, len(lines)):
        lines[index] = lines[index].strip()
        if(lines[index]):
            lines[index] = line_prefix + lines[index]

    if lines:
        lines = [line for line in lines if line]

    return linesep.join(lines) if lines else None


def is_numeric(operand):
    """ Check if given value is a number value or number saved as text

    Arguments:
        operand mixed -- value will be checked

    Returns:
        bool -- True if given value looks like a number, False otherwise
    """

    return type(operand) == int or \
        (type(operand) == str and operand.isnumeric())


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
