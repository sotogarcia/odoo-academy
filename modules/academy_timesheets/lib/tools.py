# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from re import sub as regex_replace


def truncate_name(sz, lbound, ubound, ellipsis=True):
    sz = (sz or '').strip()
    sz = regex_replace(' +', ' ', sz)

    length = len(sz)
    p1 = sz.find('.') + 1
    p2 = sz.find('.', p1) + 1

    if p2 >= lbound and p2 <= ubound:
        sz = sz[:p2] + (' ...' if ellipsis else '')
    elif p1 >= lbound and p1 <= ubound:
        sz = sz[:p1] + (' ...' if ellipsis else '')
    elif length > ubound:
        sz = sz[:ubound + 2]  # Perhaps this is the last char of the word
        last_space = sz.strip().rfind(' ')
        sz = sz[:last_space] + ('...' if ellipsis else '')

    return sz


def truncate_to_space(sz, lbound, ubound, ellipsis=True):
    sz = (sz or '').strip()
    sz = regex_replace(' +', ' ', sz)

    if len(sz) > ubound:
        copy = sz[:ubound + 2]  # Perhaps this is the last char of the word
        last_space = copy.strip().rfind(' ')
        if last_space >= lbound:
            sz = sz[:last_space] + ('...' if ellipsis else '')

    return sz
