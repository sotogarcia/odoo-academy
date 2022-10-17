# -*- coding: utf-8 -*-
""" Common

This module contains methos will be called from several models
"""

import itertools
import re
from logging import getLogger
from odoo.tools.translate import _

ABB_REGEX = r'((L|LO|D|DL|DLVO|RD|RDL|RDLVO) ?([0-9]+/[0-9]{4}))'
NUM_REGEX = r'((([0-9]+\-)?[0-9]+(, *))*([0-9]+\-)?[0-9]+)'
LAW_REGEX = r'((Ley( Orgánica)?|(Real )?Decreto( Legislativo|-Ley)?) ?([0-9]+/[0-9]{4}))'
ART_REGEX = r'(\mArt[íi]culo ({art})\M( .*)?)'

LAW_MAP = {
    'L': 'Ley',
    'LO': 'Ley Orgánica',
    'D': 'Decreto',
    'DL': 'Decreto-Ley',
    'DLVO': 'Decreto Legislativo',
    'RD': 'Real Decreto',
    'RDL': 'Real Decreto-Ley',
    'RDLVO': 'Real Decreto Legislativo',
}


_logger = getLogger(__name__)


def _interpolate(in_str):
    """Convert a string like 5-7 in a list like [5, 6, 7]

    Args:
        in_str (str): string like 5-7

    Returns:
        list: list of integers like [5, 6, 7]
    """

    values = (in_str or '').strip().split('-')

    if len(values) > 1:
        values = [int(value) for value in values]
        result = list(range(min(values), max(values) + 1))
    else:
        result = [int(in_str)]

    return result


def join_ints(value_list, separator=', '):
    """Join a given value list as if it were a list of strings

    Args:
        value_list (list): list of elements can be converted in strings
        separator (str, optional): string will be used as separator

    Returns:
        str: character string resulting from joined
    """

    return separator.join([str(item) for item in value_list])


def article_numbers(articles_str):
    """Convert a string like '3,5,5-7' in a list like [3, 5, 6, 7]

    Args:
        articles_str (str): string that matches pattern NUM_REGEX. This
        regex pattern is defined at the begining of the module file.

    Returns:
        list: list of integers from converted string
    """

    articles = []

    if articles_str:
        articles = articles_str.split(',')
        for index in range(0, len(articles)):
            articles[index] = _interpolate(articles[index])
        articles = list(itertools.chain.from_iterable(articles))
        articles = list(dict.fromkeys(articles))

    return articles


def clear_value(value):
    value = re.sub(r'[\t \r\n]+', ' ', value or '', flags=re.IGNORECASE)

    return value.strip()


def split_value(value):
    result = (None, None)

    pattern = r'^{law}$|^{num}$|^{law}\:{num}$|^{abb}$|^{abb}\:{num}$'
    pattern = pattern.format(law=LAW_REGEX, num=NUM_REGEX, abb=ABB_REGEX)
    re_match = re.match(pattern, value, flags=re.IGNORECASE)

    if re_match:
        if re_match.group(1):      # Law only
            result = (re_match.group(1), None)

        elif re_match.group(7):    # Articles only
            result = (None, re_match.group(7))

        elif re_match.group(12):   # Law and articles
            result = (re_match.group(12), re_match.group(18))

        elif re_match.group(23):   # Abbreviated law
            name = LAW_MAP[re_match.group(24).upper()]
            code = re_match.group(25)
            result = ('{} {}'.format(name, code), None)

        elif re_match.group(26):   # Abbreviated law and articles
            name = LAW_MAP[re_match.group(27).upper()]
            code = re_match.group(28)
            result = ('{} {}'.format(name, code), re_match.group(29))

    return result


def query_fetch_all_ids(model_set, sql):
    msg = _('Law pattern search with sql: {}')
    _logger.debug(msg.format(sql))

    model_set.env.cr.execute(sql)

    rows = model_set.env.cr.dictfetchall()

    return [row['id'] for row in rows]
