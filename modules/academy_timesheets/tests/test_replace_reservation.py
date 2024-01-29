# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import MissingError

from logging import getLogger

from datetime import datetime, timedelta


_logger = getLogger(__name__)


class TestReplaceReservation(TransactionCase):

    def setUp(self):
        super(TestReplaceReservation, self).setUp()

        xid = 'academy_timesheets.academy_training_session_test_1'
        self._session_1 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_1'
        self._reservation_1 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_2'
        self._reservation_2 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_3'
        self._reservation_3 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_4'
        self._reservation_4 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_6'
        self._reservation_6 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_7'
        self._reservation_7 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_nuisance_1'
        self._nuisance_1 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_nuisance_2'
        self._nuisance_2 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_nuisance_3'
        self._nuisance_3 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_nuisance_4'
        self._nuisance_4 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_nuisance_5'
        self._nuisance_5 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_nuisance_6'
        self._nuisance_6 = self.env.ref(xid)

        xid = 'academy_timesheets.academy_facility_reservation_test_nuisance_7'
        self._nuisance_7 = self.env.ref(xid)

        xid = 'academy_timesheets.facility_test_1'
        self._facility_1 = self.env.ref(xid)

        xid = 'academy_timesheets.facility_test_2'
        self._facility_2 = self.env.ref(xid)

        xid = 'academy_timesheets.facility_test_3'
        self._facility_3 = self.env.ref(xid)

        xid = 'academy_timesheets.facility_test_4'
        self._facility_4 = self.env.ref(xid)

        xid = 'academy_timesheets.facility_test_5'
        self._facility_5 = self.env.ref(xid)

        xid = 'academy_timesheets.facility_test_7'
        self._facility_7 = self.env.ref(xid)

    def test_catch_all_facilities(self):
        """
        """

        date_start = self._session_1.date_start + timedelta(days=1)
        date_stop = self._session_1.date_stop + timedelta(days=1)

        values = {'date_start': date_start, 'date_stop': date_stop}
        result = self._session_1._catch_all_facilities(values)
        expected = (self._facility_1.id, self._facility_2.id)
        obtained = tuple(result)
        message = '_catch_all_facilities with no data'
        self.assertCountEqual(expected, obtained, msg=message)

        # Append new reservation
        session_values = {
            'active': True,
            'facility_id': self._facility_5.id,
            'date_start': date_start.strftime('%Y-%m-%d HH:MM:SS'),
            'date_stop': date_stop.strftime('%Y-%m-%d HH:MM:SS'),
            'validate': True,
            'state': 'confirmed',
        }

        values.update({'reservation_ids': [(0, None, session_values)]})
        result = self._session_1._catch_all_facilities(values)
        expected = (
            self._facility_1.id, self._facility_2.id, self._facility_5.id)
        obtained = tuple(result)
        message = '_catch_all_facilities - Append new'
        self.assertCountEqual(expected, obtained, msg=message)

        # Update linked reservation
        session_values = {
            'description': datetime.now().isoformat(),
            'facility_id': self._facility_5.id
        }

        values.update({
            'reservation_ids': [(1, self._reservation_2.id, session_values)]
        })
        result = self._session_1._catch_all_facilities(values)
        expected = (self._facility_1.id, self._facility_5.id)
        obtained = tuple(result)
        message = '_catch_all_facilities - Update linked'
        self.assertCountEqual(expected, obtained, msg=message)

        # Cut the link to the linked record
        values.update({'reservation_ids': [(3, self._reservation_2.id, None)]})
        result = self._session_1._catch_all_facilities(values)
        expected = (self._facility_1.id,)
        obtained = tuple(result)
        message = '_catch_all_facilities - Cut the link'
        self.assertCountEqual(expected, obtained, msg=message)

        #  link to existing record with id = ID
        values.update({'reservation_ids': [(4, self._reservation_3.id, None)]})
        result = self._session_1._catch_all_facilities(values)
        expected = (
            self._facility_1.id, self._facility_2.id, self._facility_3.id)
        obtained = tuple(result)
        message = '_catch_all_facilities - Link to existing'
        self.assertCountEqual(expected, obtained, msg=message)

        # Remove and delete the linked reservation
        values.update({'reservation_ids': [(2, self._reservation_2.id, None)]})
        result = self._session_1._catch_all_facilities(values)
        expected = (self._facility_1.id,)
        obtained = tuple(result)
        message = '_catch_all_facilities - Remove and delete'
        self.assertCountEqual(expected, obtained, msg=message)

        # Unlink all (like using (3, ID) for all linked records)
        values.update({'reservation_ids': [(5, None, None)]})
        result = self._session_1._catch_all_facilities(values)
        expected = tuple()
        obtained = tuple(result)
        message = '_catch_all_facilities - Unlink all'
        self.assertCountEqual(expected, obtained, msg=message)

        # Replace the list of linked IDs
        seservation_set = self._reservation_3 | self._reservation_4
        values.update({'reservation_ids': [(6, None, seservation_set.ids)]})
        result = self._session_1._catch_all_facilities(values)
        expected = (self._facility_3.id, self._facility_4.id)
        obtained = tuple(result)
        message = '_catch_all_facilities - Replace the lis'
        self.assertCountEqual(expected, obtained, msg=message)

    def test_search_for_overlapping_reservations(self):
        """
        """

        date_start = self._session_1.date_start + timedelta(days=1)
        date_stop = self._session_1.date_stop + timedelta(days=1)

        values = {'date_start': date_start, 'date_stop': date_stop}
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = (self._nuisance_1.id, self._nuisance_2.id)
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations with no data'
        self.assertCountEqual(expected, obtained, msg=message)

        # Append new reservation
        session_values = {
            'active': True,
            'facility_id': self._facility_5.id,
            'date_start': date_start.strftime('%Y-%m-%d HH:MM:SS'),
            'date_stop': date_stop.strftime('%Y-%m-%d HH:MM:SS'),
            'validate': True,
            'state': 'confirmed',
        }

        values.update({'reservation_ids': [(0, None, session_values)]})
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = (
            self._nuisance_1.id, self._nuisance_2.id, self._nuisance_5.id)
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations - Append new'
        self.assertCountEqual(expected, obtained, msg=message)

        # Update linked reservation
        session_values = {
            'description': datetime.now().isoformat(),
            'facility_id': self._facility_5.id
        }

        values.update({
            'reservation_ids': [(1, self._reservation_2.id, session_values)]
        })
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = (self._nuisance_1.id, self._nuisance_5.id)
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations - Update linked'
        self.assertCountEqual(expected, obtained, msg=message)

        # Cut the link to the linked record
        values.update({'reservation_ids': [(3, self._reservation_2.id, None)]})
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = (self._nuisance_1.id,)
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations - Cut the link'
        self.assertCountEqual(expected, obtained, msg=message)

        #  link to existing record with id = ID
        values.update({'reservation_ids': [(4, self._reservation_3.id, None)]})
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = (
            self._nuisance_1.id, self._nuisance_2.id, self._nuisance_3.id)
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations - Link to existing'
        self.assertCountEqual(expected, obtained, msg=message)

        # Remove and delete the linked reservation
        values.update({'reservation_ids': [(2, self._reservation_2.id, None)]})
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = (self._nuisance_1.id,)
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations - Remove and delete'
        self.assertCountEqual(expected, obtained, msg=message)

        # Unlink all (like using (3, ID) for all linked records)
        values.update({'reservation_ids': [(5, None, None)]})
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = tuple()
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations - Unlink all'
        self.assertCountEqual(expected, obtained, msg=message)

        # Replace the list of linked IDs
        seservation_set = self._reservation_3 | self._reservation_4
        values.update({'reservation_ids': [(6, None, seservation_set.ids)]})
        result = self._session_1._search_for_overlapping_reservations(values)
        expected = (self._nuisance_3.id, self._nuisance_4.id)
        obtained = tuple(result.ids)
        message = '_search_for_overlapping_reservations - Replace the lis'
        self.assertCountEqual(expected, obtained, msg=message)

    def test_adjust_existing_facility_reservations(self):

        date_start = self._session_1.date_start + timedelta(days=1)
        date_stop = self._session_1.date_stop + timedelta(days=1)

        values = {'date_start': date_start, 'date_stop': date_stop}

        # Unlink all (5)
        values.update({'reservation_ids': [(5, None, None)]})
        result = self._session_1._adjust_existing_facility_reservations(values)
        message = '_adjust_existing_facility_reservations - Unlink all'
        self.assertFalse(result, msg=message)

        # Replace the list of linked IDs (6)
        seservation_set = self._reservation_3 | self._reservation_7
        values.update({'reservation_ids': [(6, None, seservation_set.ids)]})
        result = self._session_1._adjust_existing_facility_reservations(values)
        expected = self._nuisance_3
        message = '_adjust_existing_facility_reservations - Replace the lis'
        self.assertEqual(expected, result, msg=message)
        self.assertEqual(
            self._nuisance_3.date_start, date_stop)

        # Remove and delete the linked reservation (2)
        # Cut the link to the linked record (3)
        # Append new reservation (0)
        # link to existing record with id = ID
        session_values = {
            'active': True,
            'facility_id': self._facility_5.id,
            'date_start': date_start.strftime('%Y-%m-%d HH:MM:SS'),
            'date_stop': date_stop.strftime('%Y-%m-%d HH:MM:SS'),
            'validate': True,
            'state': 'confirmed',
        }

        values.update({
            'reservation_ids': [
                (2, self._reservation_1.id, None),
                (3, self._reservation_2.id, None),
                (0, None, session_values),
                (4, self._reservation_6.id, None)
            ]
        })
        result = self._session_1._adjust_existing_facility_reservations(values)
        message = '_adjust_existing_facility_reservations - m2m op: 2, 3, 0, 4'
        expected = self._nuisance_5
        self.assertEqual(expected, result, msg=message)
        self.assertEqual(self._nuisance_5.date_start, date_stop)
        with self.assertRaises(MissingError):
            self._nuisance_6.facility_id

        # Update linked reservation
        session_values = {
            'description': datetime.now().isoformat(),
            'facility_id': self._facility_4.id
        }

        values.update(
            {'reservation_ids': [(1, self._reservation_1, session_values)]})
        result = self._session_1._adjust_existing_facility_reservations(values)
        expected = self._nuisance_2 | self._nuisance_4
        message = '_search_for_overlapping_reservations - Update linked'
        self.assertEqual(expected, result, msg=message)
