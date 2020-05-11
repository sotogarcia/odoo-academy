# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Name of model

This module contains unit test for academy.training.session.wizard model
"""

from logging import getLogger
from datetime import date, datetime, time, timedelta

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, E0401
from odoo.tests.common import TransactionCase
from odoo import fields


# pylint: disable=locally-disabled, R0904, C0103, W0212, C0111
class TestAcademyTrainingSessionWizard(TransactionCase):
    """ This class contains the unit tests for 'test.academy.training.session.wizard'.

        Tests:
          - item_name: Checks if the item_name works properly
    """

    def setUp(self):
        """ Prepair unit tests """

        super(TestAcademyTrainingSessionWizard, self).setUp()

        self._wizard_obj = self.env['academy.training.session.wizard']
        self._teacher_id = None
        self._start_date = date(2018, 10, 1)


    # pylint: disable=locally-disabled, W0102
    def _new_wizard(self, wdata={}, ldata={}):
        start_date = fields.Date.to_string(self._start_date)

        values = {
            'following' : ldata.get('following', False),
            'start_date': ldata.get('start_date', start_date),
            'start_time': ldata.get('start_time', 9.0),
            'duration'  : ldata.get('duration', 5.0),
            'maximum'   : ldata.get('maximum', 5.0),
            'incomplete': ldata.get('incomplete', 'next')
        }

        wizard_set = self._wizard_obj .create(wdata)
        wizard_set._onchange_training_action_id()

        line_set = wizard_set.wizard_line_ids.sorted( \
            key=lambda p: (p.training_module_id.sequence, p.sequence))

        line_set[0].update(values)

        wizard_set.training_lesson_ids.unlink()

        return wizard_set, line_set


    @staticmethod
    def _line_headers():
        return (
            'Training Unit',
            'Imparted',
            'Following',
            'Start date',
            'Start time',
            'Duration',
            'Maximum',
            'Incomplete'
        )

    @staticmethod
    def _lesson_headers():
        return (
            'Code',
            'Action',
            'Module',
            'Start_date',
            'Duration'
        )


    @staticmethod
    def _line_to_tuple(line):
        return (
            str(line.training_unit_id.name),
            str(line.imparted),
            str(line.following),
            str(line.start_date),
            str(line.start_time),
            str(line.duration),
            str(line.maximum),
            str(line.incomplete)
        )


    @staticmethod
    def _lesson_to_tuple(lesson):
        return (
            str(lesson.code),
            str(lesson.training_action_id.id),
            str(lesson.training_module_id.id),
            str(lesson.start_date),
            str(lesson.duration)
        )


    def _build_line(self, line=False):
        patern = '{:20}  {:^8}  {:^9}  {:^10}  {:^10}  {:^8}  {:^7}  {:^10}'

        if line:
            result = patern.format(*self._line_to_tuple(line))
        else:
            result = patern.format(*self._line_headers())

        return result


    def _build_lesson(self, lesson=False):
        patern = '{:10}  {:^10}  {:^10}  {:^10}  {:^10}'

        if lesson:
            result = patern.format(*self._lesson_to_tuple(lesson))
        else:
            result = patern.format(*self._lesson_headers())

        return result


    def _log_wizard_data(self, wizard_set, msg='', result=None):
        msg = '{}'.format(msg)

        wizard_set.ensure_one()

        msg = msg + '\nStart date     : ' + str(wizard_set.start_date)
        msg = msg + '\nStart time     : ' + str(wizard_set.start_time)
        msg = msg + '\nInterval       : ' + str(wizard_set.interval)
        msg = msg + '\nRrule type     : ' + wizard_set.rrule_type
        if wizard_set.rrule_type == 'weekly':
            msg = msg + '\nWeekdays       : ' + str(wizard_set._get_weekdays())
        elif wizard_set.rrule_type == 'monthly':
            msg = msg + '\nMonth_by       : ' + wizard_set.month_by
            if wizard_set.month_by == 'date':
                msg = msg + '\n  Month day    : ' + str(wizard_set.day)
            else:
                msg = msg + '\n  Month byday  : ' + wizard_set.byday
                msg = msg + '\n  weeklist     : ' + wizard_set.week_list

        line_set = wizard_set.wizard_line_ids.sorted( \
            key=lambda p: (p.training_module_id.sequence, p.sequence))

        if line_set:
            msg = msg + '\n' + self._build_line()
            for line in line_set:
                msg = msg + '\n' + self._build_line(line)

        if wizard_set.training_lesson_ids:
            msg = msg + '\n' + self._build_lesson()
            for lesson in wizard_set.training_lesson_ids:
                msg = msg + '\n' + self._build_lesson(lesson)

        if result:
            msg = msg + '\n' + result

        return msg


    @staticmethod
    def _set_weekdays(wizard, weekdays):
        """ Returns a zero start numeric list that represents the chosen weekdays
        """
        fieldnames = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']

        index = 0
        for field in fieldnames:
            setattr(wizard, field, bool(index in weekdays))
            index = index + 1


    def _check_lessons(self, wizard_set, expected, remove=False):
        """
        expected = [
            {
            'start_date'        : fields.Date,
            'start_time'        : float,
            'duration'          : float,
            'teacher_id'        : int
            },
            ...
        ]
        """

        wizard_str = self._log_wizard_data(wizard_set)
        lesson_set = wizard_set.training_lesson_ids

        msg = 'There are an unexpected number of lessons %s de %s\n%s'
        self.assertTrue(len(lesson_set) == len(expected), \
            msg % (len(lesson_set), len(expected), wizard_str))

        for index, lesson in enumerate(lesson_set): # pylint: disable=locally-disabled, W0612
            expect = expected[index]
            start_time = self._date_time_str(expect['start_date'], expect['start_time'])

            msg = 'Lesson %s start time not match\n%s' % (str(index + 1), wizard_str)
            self.assertEqual(lesson.start_date, start_time, msg)

            msg = 'Lesson %s duration not match' % str(index + 1)
            self.assertEqual(lesson.duration, expect['duration'], msg)

            msg = 'Lesson %s duration not match' % str(index + 1)
            self.assertEqual(lesson.teacher_id, expect['teacher_id'], msg)

        if remove:
            lesson_set.unlink()


    def _date_time_str(self, start_date, start_time):

        if isinstance(start_date, str):
            start_date = fields.Date.from_string(start_date)

        start_time = self._wizard_obj._float_to_time(start_time)

        start_time = datetime.combine(start_date, start_time)
        start_time = fields.Datetime.to_string(start_time)

        return start_time


        # duration > maximum


    # ------------------------ TEST FIRST VALID DATE --------------------------

    def test__get_first_valid_date_daily_and_yearly(self):
        """ Unit tests for _get_first_valid_date
            daily  2018-10-01
            yearly 2016-10-01
            yearly 2016-02-29
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        wizard_set.rrule_type = 'daily'
        expected = date(2018, 10, 1)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.rrule_type = 'yearly'
        expected = date(2018, 10, 1)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.rrule_type = 'yearly'
        expected = date(2016, 2, 29)
        result = wizard_set._get_first_valid_date(date29)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


    def test__get_first_valid_date_weekly(self):
        """ Unit tests for _get_first_valid_date
            weekly 2018-10-01 [mo]
            weekly 2018-10-01 [tu]
            weekly 2018-10-05 [mo]
            weekly 2018-10-31 [th]
            weekly 2018-10-31 [mo]
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        wizard_set.rrule_type = 'weekly'
        self._set_weekdays(wizard_set, [0])
        expected = date(2018, 10, 1)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        self._set_weekdays(wizard_set, [1])
        expected = date(2018, 10, 2)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        self._set_weekdays(wizard_set, [0])
        expected = date(2018, 10, 8)
        result = result = wizard_set._get_first_valid_date(date05)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        self._set_weekdays(wizard_set, [2])
        expected = date(2018, 10, 31)
        result = wizard_set._get_first_valid_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        self._set_weekdays(wizard_set, [0])
        expected = date(2018, 11, 5)
        result = wizard_set._get_first_valid_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


    def test__get_first_valid_date_monthly_day(self):
        """ Unit tests for _get_first_valid_date
            monthly date 2018-10-01 1st mo
            monthly date 2018-10-01 2st mo
            monthly date 2018-10-01 last mo
            monthly date 2018-10-31 last[we]
            monthly date 2018-10-31 1st mo
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        wizard_set.rrule_type = 'monthly'
        wizard_set.month_by = 'day'

        wizard_set.week_list = 'WD0'
        wizard_set.byday = '1'
        expected = date(2018, 10, 1)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.week_list = 'WD0'
        wizard_set.byday = '2'
        expected = date(2018, 10, 8)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.week_list = 'WD0'
        wizard_set.byday = '-1'
        expected = date(2018, 10, 29)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.week_list = 'WD2'
        wizard_set.byday = '-1'
        expected = date(2018, 10, 31)
        result = wizard_set._get_first_valid_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.week_list = 'WD0'
        wizard_set.byday = '1'
        expected = date(2018, 11, 5)
        result = wizard_set._get_first_valid_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

    def test__get_first_valid_date_monthly_date(self):
        """ Unit tests for _get_first_valid_date

            monthly date 2018-10-01 [1]
            monthly date 2018-10-01 [5]
            monthly date 2018-10-05 [1]
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        wizard_set.rrule_type = 'monthly'
        wizard_set.month_by = 'date'

        wizard_set.day = 1
        expected = date(2018, 10, 1)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set, str(date01))
        self.assertEqual(result, expected, msg)

        wizard_set.day = 5
        expected = date(2018, 10, 5)
        result = wizard_set._get_first_valid_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.day = 1
        expected = date(2018, 11, 1)
        result = wizard_set._get_first_valid_date(date05)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


    # ----------------------------- _NEXT_DATE --------------------------------

    def test__next_date_dayly_and_yearly(self):
        """ Unit tests for _next_date
            daily  2018-10-01
            yearly 2016-10-01
            yearly 2016-02-29
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        wizard_set.rrule_type = 'daily'
        expected = date(2018, 10, 2)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.rrule_type = 'yearly'
        expected = date(2019, 10, 1)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        wizard_set.rrule_type = 'yearly'
        expected = date(2017, 2, 28)
        result = wizard_set._next_date(date29)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


    def test__next_date_weekly(self):
        """ Unit tests for _next_date
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        # Next weekday in week is valid
        wizard_set.rrule_type = 'weekly'
        self._set_weekdays(wizard_set, [0, 1])
        expected = date(2018, 10, 2)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # Next weekday in week is not valid
        self._set_weekdays(wizard_set, [0, 2])
        expected = date(2018, 10, 3)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # Previous and current weekday in week is valid, not the following
        self._set_weekdays(wizard_set, [3, 4])
        expected = date(2018, 10, 11)
        result = result = wizard_set._next_date(date05)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # Only current weekday is valid
        self._set_weekdays(wizard_set, [0])
        expected = date(2018, 10, 8)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


    def test__next_date_monthly_day(self):
        """ Unit tests for _next_date
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        wizard_set.rrule_type = 'monthly'
        wizard_set.month_by = 'day'

        # First monday in month to first monday in month
        wizard_set.week_list = 'WD0'
        wizard_set.byday = '1'
        expected = date(2018, 11, 5)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


        # First monday in month to second monday in month
        wizard_set.week_list = 'WD0'
        wizard_set.byday = '2'
        expected = date(2018, 10, 8)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # First monday in month to first sunday in month
        wizard_set.week_list = 'WD6'
        wizard_set.byday = '1'
        expected = date(2018, 10, 7)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # First friday in month to first monday in month
        wizard_set.week_list = 'WD0'
        wizard_set.byday = '1'
        expected = date(2018, 11, 5)
        result = wizard_set._next_date(date05)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # First monday in month to last monday in month
        wizard_set.week_list = 'WD0'
        wizard_set.byday = '-1'
        expected = date(2018, 10, 29)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # Last wednesday in month to last wednesday in month
        wizard_set.week_list = 'WD2'
        wizard_set.byday = '-1'
        expected = date(2018, 11, 28)
        result = wizard_set._next_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # Last wednesday in month to first wednesday in month
        wizard_set.week_list = 'WD2'
        wizard_set.byday = '1'
        expected = date(2018, 11, 7)
        result = wizard_set._next_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


    def test__next_date_monthly_date(self):
        """ Unit tests for _next_date
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()

        date01 = date(2018, 10, 1)
        date29 = date(2016, 2, 29)
        date05 = date(2018, 10, 5)
        date31 = date(2018, 10, 31)

        wizard_set.rrule_type = 'monthly'
        wizard_set.month_by = 'date'

        # Current day is before valid date
        wizard_set.day = 2
        expected = date(2018, 10, 2)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set, str(date01))
        self.assertEqual(result, expected, msg)

        # Current day is a valid date
        wizard_set.day = 1
        expected = date(2018, 11, 1)
        result = wizard_set._next_date(date01)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # Current day is after a valid date
        wizard_set.day = 1
        expected = date(2018, 11, 1)
        result = wizard_set._next_date(date05)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # February, 29 (non leap-year)
        date31 = date(2018, 1, 31)
        wizard_set.day = 31
        expected = date(2018, 2, 28)
        result = wizard_set._next_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # February, 29 (non leap-year, case 2)
        date29 = date(2018, 1, 29)
        wizard_set.day = 29
        expected = date(2018, 2, 28)
        result = wizard_set._next_date(date29)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)

        # February, 29 (leap-year)
        date31 = date(2016, 1, 31)
        wizard_set.day = 31
        expected = date(2016, 2, 29)
        result = wizard_set._next_date(date31)
        msg = self._log_wizard_data(wizard_set)
        self.assertEqual(result, expected, msg)


    # -------------------------- COMPLETE SESSION -----------------------------

    def test__complete_session(self):
        """ Unit tests for _next_date

          duration  remaining  maximum
             <          =         =
             >          =         =
             3          1         2
             2          1         3
             2          3         1
             3          2         1
        """

        # pylint: disable=locally-disabled, W0612
        wizard_set, line_set = self._new_wizard()
        line = line_set[0]
        last_date = datetime.combine(date.today(), time(9, 0, 0))
        msg = '_complete_session: line.duration %s line.maximum %s remaining %s'
        last_date_str = fields.Datetime.to_string(last_date)
        last_date_str2 = fields.Datetime.to_string(last_date + timedelta(hours=1))
        last_date_str3 = fields.Datetime.to_string(last_date + timedelta(hours=2))

        # Session length 1, hours in line 1, empty 1
        wizard_set.duration, line.maximum, remaining = (1, 1, 1)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str, 1.0, 0.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )

        # Session length 1, hours in line 2, empty 1
        wizard_set.duration, line.maximum, remaining = (1, 2, 1)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str, 1.0, 0.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )

        # # Session length 1, hours in line 1, empty 2
        # wizard_set.duration, line.maximum, remaining = (1, 1, 2)
        # leftover = wizard_set._complete_session(line, last_date, remaining)
        # lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        # self.assertRaises(ValueError)

        # # Session length 1, hours in line 2, empty 2
        # wizard_set.duration, line.maximum, remaining = (1, 2, 2)
        # leftover = wizard_set._complete_session(line, last_date, remaining)
        # lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        # self.assertRaises(ValueError)

        # # Session length 1, hours in line 3, empty 2
        # wizard_set.duration, line.maximum, remaining = (1, 3, 2)
        # leftover = wizard_set._complete_session(line, last_date, remaining)
        # lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        # self.assertRaises(ValueError)

        # # Session length 1, hours in line 2, empty 3
        # wizard_set.duration, line.maximum, remaining = (1, 2, 3)
        # leftover = wizard_set._complete_session(line, last_date, remaining)
        # lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        # self.assertRaises(ValueError)

        # # Session length 1, hours in line 3, empty 3
        # wizard_set.duration, line.maximum, remaining = (1, 3, 3)
        # leftover = wizard_set._complete_session(line, last_date, remaining)
        # lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        # self.assertRaises(ValueError)

        # Session length 2, hours in line 1, empty 1
        wizard_set.duration, line.maximum, remaining = (2, 1, 1)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str2, 1.0, 0.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )

        # Session length 2, hours in line 2, empty 1
        wizard_set.duration, line.maximum, remaining = (2, 2, 1)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str2, 1.0, 0.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )

        # Session length 2, hours in line 3, empty 1
        wizard_set.duration, line.maximum, remaining = (2, 3, 1)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str2, 1.0, 0.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )

        # Session length 2, hours in line 1, empty 2
        wizard_set.duration, line.maximum, remaining = (2, 1, 2)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str, 1.0, 1.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )

        # # Session length 2, hours in line 1, empty 3
        # wizard_set.duration, line.maximum, remaining = (2, 1, 3)
        # leftover = wizard_set._complete_session(line, last_date, remaining)
        # lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        # self.assertRaises(ValueError)

        # Session length 3, hours in line 2, empty 1
        wizard_set.duration, line.maximum, remaining = (3, 2, 1)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str3, 1.0, 0.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )

        # Session length 3, hours in line 1, empty 2
        wizard_set.duration, line.maximum, remaining = (3, 1, 2)
        leftover = wizard_set._complete_session(line, last_date, remaining)
        lesson = wizard_set.training_lesson_ids.sorted(key='id', reverse=True)[0]
        self.assertTupleEqual(
            (lesson.start_date, lesson.duration, leftover),
            (last_date_str2, 1.0, 1.0),
            msg=msg % (line.duration, line.maximum, remaining)
        )


    # ---------------------------- PROCESS LINE -------------------------------

    def test__process_line_not_lines(self):
        pass

    def test__process_line_one_line(self):
        # pylint: disable=locally-disabled, W0612

        ldata = {
            'following' : False,
            'start_date': fields.Date.to_string(self._start_date),
            'start_time': 9.0,
            'duration'  : 5.0,
            'maximum'   : 5.0,
            'incomplete': 'next',
            'teacher_id': self._teacher_id
        }

        msg = '_process_line: lesson.duration %s lesson.duration %s'
        wizard_set, line_set = self._new_wizard(ldata=ldata)

        wizard_set.write({'wizard_line_ids': [(2, line_set[1].id, None)]})
        line_set = wizard_set.wizard_line_ids

        wizard_set.execute()
        self._check_lessons(
            wizard_set,
            [{
                'start_date' : line_set.start_date,
                'start_time' : line_set.start_time,
                'duration'   : line_set.duration,
                'teacher_id' : line_set.teacher_id
            }],
            True
        )

        line_set.maximum = 4
        wizard_set.execute()
        self._check_lessons(
            wizard_set,
            [{
                'start_date' : line_set.start_date,
                'start_time' : line_set.start_time,
                'duration'   : 4,
                'teacher_id' : line_set.teacher_id
            }],
            True
        )

        line_set.maximum = 6
        wizard_set.execute()
        self._check_lessons(
            wizard_set,
            [{
                'start_date' : line_set.start_date,
                'start_time' : line_set.start_time,
                'duration'   : line_set.duration,
                'teacher_id' : line_set.teacher_id
            }, {
                'start_date' : fields.Date.to_string(self._start_date + timedelta(days=1)),
                'start_time' : line_set.start_time,
                'duration'   : 1,
                'teacher_id' : line_set.teacher_id
            }],
            True
        )


