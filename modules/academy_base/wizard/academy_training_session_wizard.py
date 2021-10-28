# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" AcademyTrainingSessionWizard

This module contains the academytrainingsessionwizard an unique Odoo model
which contains all AcademyTrainingSessionWizard attributes and behavior.

This model is a wizard to create all sessions needed for a module

Classes:
    AcademyTrainingSessionWizard: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

    Inside this class can be, in order, the following attributes and methods:
    * Object attributes like name, description, inheritance, etc.
    * Entity fields with the full definition
    * Computed fields and required computation methods
    * Events (@api.onchange) and other field required methods like computed
    domain, defaul values, etc...
    * Overloaded object methods, like create, write, copy, etc.
    * Public object methods will be called from outside
    * Private auxiliary methods not related with the model fields, they will
    be called from other class methods


Todo:
    * byday shoud has a ('5', 'Fifth'), selection entry and this should be
    considered in _get_first_valid_date method (this is not easy).
    * _float_to_time should convert milliseconds

    **IMPORTANT**:
        _float_to_time: this method should use microseconds too
        **OBJETIVO** definir bien los valores de retorno de cada funnción
        **OBJETIVO** remaining debe ser positivo o negativo de modo que valga para ambos

"""


from logging import getLogger
from datetime import datetime, date, time, timedelta
from calendar import Calendar, monthrange
from math import ceil

# pylint: disable=locally-disabled, E0401
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903, R0902, E1101
class AcademyTrainingSessionWizard(models.TransientModel):
    """ This model is a wizard to create all sessions needed for an unit

    Fields:
    """


    _name = 'academy.training.session.wizard'
    _description = u'Academy training session wizard'

    _rec_name = 'id'
    _order = 'id ASC'


    # ---------------------------- ENTITY FIELDS ------------------------------

    training_action_id = fields.Many2one(
        string='Training action',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_training_action_id(), # pylint: disable=locally-disabled, W0212
        help='Choose a training action',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    interval = fields.Integer(
        string='Repeat every',
        required=False,
        readonly=False,
        index=False,
        default=1,
        help='Repeat every (Days/Week/Month/Year)'
    )

    rrule_type = fields.Selection(
        string='Recurrence',
        required=True,
        readonly=False,
        index=False,
        default='weekly',
        help='Let the event automatically repeat at that interval',
        selection=[
            ('daily', 'Day(s)'),
            ('weekly', 'Week(s)'),
            ('monthly', 'Month(s)'),
            ('yearly', 'Year(s)')
        ]
    )

    end_type = fields.Selection(
        string='End type',
        required=True,
        readonly=False,
        index=False,
        default='count',
        help='End type',
        selection=[
            ('count', 'Number of repetitions'),
            ('end_date', 'End date')
        ]
    )

    count = fields.Integer(
        string='Repeat',
        required=False,
        readonly=False,
        index=False,
        default=1,
        help='Repeat x times'
    )

    mo = fields.Boolean(
        string='Monday',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Monday'
    )

    tu = fields.Boolean(
        string='Tuesday',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Tuesday'
    )

    we = fields.Boolean(
        string='Wednesday',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Wednesday'
    )

    th = fields.Boolean(
        string='Thursday',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Thursday'
    )

    fr = fields.Boolean(
        string='Friday',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Monday'
    )

    sa = fields.Boolean(
        string='Saturday',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Saturday'
    )

    su = fields.Boolean(
        string='Sunday',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Sunday'
    )

    month_by = fields.Selection(
        string='Month by',
        required=True,
        readonly=False,
        index=False,
        default='date',
        help='Month by',
        selection=[
            ('date', 'Date of month'),
            ('day', 'Day of month')
        ]
    )

    day = fields.Integer(
        string='Date of month',
        required=False,
        readonly=False,
        index=False,
        default=1,
        help='Date of month'
    )

    week_list = fields.Selection(
        string='Weekday',
        required=True,
        readonly=False,
        index=False,
        default='WD0',
        help='Week day',
        selection=[
            ('WD0', 'Monday'),
            ('WD1', 'Tuesday'),
            ('WD2', 'Wednesday'),
            ('WD3', 'Thursday'),
            ('WD4', 'Friday'),
            ('WD5', 'Saturday'),
            ('WD6', 'Sunday')
        ]
    )

    byday = fields.Selection(
        string='By day',
        required=True,
        readonly=False,
        index=False,
        default='1',
        help='By day',
        selection=[
            ('1', 'First'),
            ('2', 'Second'),
            ('3', 'Third'),
            ('4', 'Fourth'),
            ('-1', 'Last')
        ]
    )

    final_date = fields.Date(
        string='Repeat until',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.context_today(self), # pylint: disable=locally-disabled, W0108
        help=False
    )

    state = fields.Selection(
        string='State',
        required=False,
        readonly=False,
        index=False,
        default='step1',
        help='Current wizard state',
        selection=[
            ('step1', 'Training action'),
            ('step2', 'Training units'),
            ('step3', 'Time interval')
        ]
    )

    start_date = fields.Date(
        string='Start date',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False
    )

    start_time = fields.Float(
        string='Start time',
        required=False,
        readonly=False,
        index=False,
        default=9.0,
        digits=(16, 2),
        help='Start time '
    )

    duration = fields.Float(
        string='Duration',
        required=True,
        readonly=False,
        index=False,
        default=5.0,
        digits=(16, 2),
        help=False
    )


    # --------------------------- COMPUTED FIELDS -----------------------------

    # IMPORTANT!
    # Following fields should be a computed field but instead I have used an
    # @api.onchange (see below) because I need compute field domain at the
    # same time. Even so, the non called compute method is down the field and
    # it's used by the onchange method.

    training_unit_ids = fields.Many2many(
        string='Training units',
        required=False,
        readonly=True,
        index=False,
        default=lambda self: self._default_training_unit_ids(), # pylint: disable=locally-disabled, W0212
        help=False,
        comodel_name='academy.training.module',
        relation='academy_training_session_wizard_trainining_module_rel',
        column1='session_wizard_id',
        column2='training_unit_id',
        domain=[],
        context={},
        limit=None,
    )

    @api.depends('training_action_id')
    def _default_training_unit_ids(self):
        unit_set = self._get_units()
        return [(6, None, unit_set.ids)]


    wizard_line_ids = fields.One2many(
        string='Wizard lines',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_wizard_line_ids(),   # pylint: disable=locally-disabled, W0212
        help=False,
        comodel_name='academy.training.session.wizard.line',
        inverse_name='session_wizard_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    def _default_wizard_line_ids(self):
        unit_set = self._get_units()

        unit_lines = []
        index = 1
        for unit in unit_set:
            unit_line = self._wizard_line_to_append(unit, index)
            if unit_line:
                unit_lines.append(unit_line)
                index = index + 1

        return unit_lines


    training_lesson_ids = fields.Many2many(
        string='Training lessons',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.lesson',
        relation='academy_training_session_wizard_training_lesson_rel',
        column1='session_wizard_id',
        column2='training_lesson_id',
        domain=[],
        context={},
        limit=None
    )


    # ----------------------- REQUIRED FIELD METHODS --------------------------

    def _default_duration(self):    # pylint: disable=locally-disabled, R0201
        hour = time(5, 0, 0)
        hours = datetime.combine(date.min, hour) - datetime.min
        return hours.seconds / 3600.0


    def _default_start_time(self):   # pylint: disable=locally-disabled, R0201
        hour = time(9, 0, 0)
        hours = datetime.combine(date.min, hour) - datetime.min
        return hours.seconds / 3600.0


    def _default_training_action_id(self):
        action_domain = []
        action_obj = self.env['academy.training.action']
        action_set = action_obj.search(action_domain, \
            offset=0, limit=1, order='create_date DESC', count=False)

        return action_set

    # --------------------------- ONCHANGE EVENTS -----------------------------

    @api.onchange('training_action_id')
    def _onchange_training_action_id(self):

        self.wizard_line_ids = [(5, None, None)]

        if self.training_action_id:

            self.training_unit_ids = self._default_training_unit_ids()
            self.wizard_line_ids = self._default_wizard_line_ids()

            self.state = 'step2'
            # pylint: disable=locally-disabled, E1101
            domain = [('id', '=', self.wizard_line_ids.mapped('id'))]

        else:
            self.training_unit_ids = [(5, None, None)]
            self.wizard_line_ids = [(5, None, None)]
            domain = [('id', '=', -1)]
            self.state = 'step1'

        return {
            'domain': {'wizard_line_ids': domain}
        }


    @api.onchange('wizard_line_ids')
    def _onchange_wizard_line_ids(self):
        action_set = self.training_action_id
        unit_set = self.wizard_line_ids

        if unit_set:
            hours = unit_set.mapped('duration')
            self.count = int(sum(hours) / 2)
        elif action_set:
            self.state = 'step2'
        else:
            self.state = 'step1'


    @api.onchange('state')
    def _onchange_state(self):
        if not self.training_action_id:
            self.state = 'step1'
        elif not self.wizard_line_ids and self.state not in ('step1', 'step2'):
            self.state = 'step2'


    # --------------------------- PUBLIC METHODS ------------------------------


    def execute(self):
        """ Wizard execute button method """

        #STEP 1: Ensure set has only one record
        self.ensure_one()

        line_set = self.wizard_line_ids.sorted(lambda item: item.sequence)

        assert line_set[0].start_date, \
            _('First line start date is required')

        to_complete = 0

        self.start_date = line_set[0].start_date
        self.start_time = line_set[0].start_time
        self.duration = line_set[0].duration

        current_date = fields.Date.from_string(line_set[0].start_date)
        to_complete = 0
        for line in line_set:

            current_date, to_complete = \
                self._process_line(line, current_date, to_complete)

            if line.incomplete != 'next':
                to_complete = 0


    # -------------------------- AUXILIARY METHODS ----------------------------

    @staticmethod
    def _float_to_time(num, delta=False):
        """ Converts given float time to a valid python time

        @return (tim): python valid time struct
        """

        minu = num % 1 * 60

        hour = int(num)
        seco = int(minu % 1 * 60)
        minu = int(minu)

        if delta:
            result = timedelta(hours=hour, minutes=minu, seconds=seco)
        else:
            result = time(hour, minu, seco)

        return result


    def _get_units(self):
        """ Search all training training units (final training modues)
        and they are relatated whith chosen training action

        @return (academy.training.mudule): sorted recordset with all units
        in chosen training action.
        """

        action_id = self.training_action_id
        activi_id = action_id.training_activity_id
        compet_ids = activi_id.mapped('competency_unit_ids')
        module_ids = compet_ids.mapped('training_module_id')

        unit_set = self.env['academy.training.module']
        for mod_id in module_ids:
            if mod_id.training_unit_ids:
                unit_set = unit_set + mod_id.training_unit_ids
            else:
                unit_set = unit_set + mod_id

        return unit_set.sorted( \
            key=lambda p: (p.training_module_id.sequence, p.sequence))


    def _wizard_line_to_append(self, unit, sequence):
        """ Returns a valid One2many append operation can be used to add
        the given wizard line to wizard_line_ids field

        @return (tuple): python Many2many valid operation line
        """

        unit_set = self.env['academy.training.module']
        imparted = unit_set.get_imparted_hours_for( \
                    self.training_action_id.id, unit.id)
        if (unit.ownhours - imparted) <= 0:
            return False

        start_date = fields.Date.today() if sequence == 1 else None
        following = False if sequence == 1 else True

        if self.training_action_id:
            teacher_id = self.training_action_id.tuttor_id
        else:
            teacher_id = None

        values = {
            'session_wizard_id' : self.id,
            'training_unit_id'  : unit.id,
            'sequence'          : sequence,
            'following'         : following,
            'start_date'        : start_date,
            'start_time'        : 9.0,
            'duration'          : 5.0,
            'maximum'           : unit.ownhours - imparted,
            'incomplete'        : 'next',
            'teacher_id'        : teacher_id.id if teacher_id else None
        }

        return (0, 0, values)


    @staticmethod
    def _get_start_date(line, last_date):
        """ Returns line start date if it not follow previous line or given
        current date.

        @return (date): return python valid start date
        """

        if line.following:
            result = last_date
        else:
            result = fields.Date.from_string(line.start_date)

        return result


    def _get_start_time(self, line):
        """ Returns line start time if it not follow previous line or given
        start time

        @return (float): float start time
        """

        return line.start_time if not line.following else self.start_time


    def _get_chosen_weekday(self):
        """ Get string value from self.week_list selection field and returns
        a numerical value. This will be the ZERO index of the weekday

        @return (integer): 0 => Monday, ..., 6 => Sunday
        """

        return safe_eval(self.week_list[-1:])


    def _get_chosen_weekday_position(self):
        """ Get string value from self.byday selection field and returns
        a numerical value. This value will be a ZERO based nth weekday
        position in month or -1 to designate the last day of month
        """
        pos = safe_eval(self.byday)

        return max(pos - 1, -1)


    def _get_time_step(self):
        """ Returns the interval will be used to compute next session date
        """

        num = self.interval

        if self.rrule_type == 'weekly':
            step = relativedelta(weeks=num)
        elif self.rrule_type == 'monthly':
            step = relativedelta(months=num)
        elif self.rrule_type == 'yearly':
            step = relativedelta(years=num)
        else:
            step = relativedelta(days=num)

        return step


    def _get_weekdays(self):
        """ Returns a zero start numeric list that represents the chosen weekdays
        """
        available = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
        checked = []

        for field in available:
            if getattr(self, field):
                checked.append(available.index(field))

        return checked


    def _get_week_dates(self, date_inside, count, mindate=date.min):
        """ Get all dates in the same week as the given date. Optionally,
        you can specify that weekdays will be included.

        @date_inside (date)  : date within the week
        @count           : maximun number of dates to return
        @weekdays (list): week days [0-6](mo-su) will be included
        """

        weekdays = self._get_weekdays()

        weekday = date_inside.weekday()
        mo = date_inside - relativedelta(days=weekday)
        su = date_inside + relativedelta(days=6-weekday)

        dates = []
        for ordinal in range(mo.toordinal(), su.toordinal() + 1):
            current = date.fromordinal(ordinal)
            if mindate <= current and count > 0:
                if current.weekday() in weekdays:
                    dates.append(current)
                    count = count - 1

        return dates


    def _get_first_valid_date(self, start_date):
        """ Returns the first date can be used as next session date
            - daily           start_date
            - weekly          firth match in range 0-8 days
            - monthly date    start_date or next month match day
            - monthly day     match in this month if it's less or equal
            to start date or match in next month
            - yearly          start_date
        """

        result = start_date
        weekdays = self._get_weekdays()
        last_day_of_month = monthrange(start_date.year, result.month)[1]
        offset = 0

        if self.rrule_type == 'weekly':
            while offset < 8 and result.weekday() not in weekdays:
                result = start_date + relativedelta(days=offset)
                offset = offset + 1

        elif self.rrule_type == 'monthly':
            if self.month_by == 'date':
                searched = min(self.day, last_day_of_month)
                result = result.replace(day=searched)
                if start_date.day > searched:
                    result = result + relativedelta(months=1)
            else:
                result = self._get_month_nth_weekday(result)
                if not result or result < start_date:
                    result = result + relativedelta(months=1)
                    result = self._get_month_nth_weekday(result)

        elif self.rrule_type == 'yearly':
            pass
        else:
            pass

        return result


    def _get_month_nth_weekday(self, in_date):
        """ Returns ZERO based nth date in month which weekday is the same
        as given (First monday, first sunday, second sunday etc...)

        @param in_date (date): random date in month
        @param weekday (int) : weekday index (0 --> Monday, ..., 6 --> Sunday)
        @param nth (int)     : number of weekday match (-1 --> Last, 0 --> First,...)
        """

        cal = Calendar(firstweekday=0)

        weekday = self._get_chosen_weekday()
        nth = self._get_chosen_weekday_position()

        month = in_date.month
        datelist = cal.itermonthdates(in_date.year, month)

        msg = 'nth ({}) param can not be less than -1 in _get_month_nth_weekday'
        assert nth >= -1, msg.format(nth)


        valid = [
            item for item in datelist \
            if item.weekday() == weekday and item.month == month
        ]

        return valid[nth] if len(valid) >= nth else None


    def _next_weekday(self, indate):
        """ Returns the next valid week day that follows the given date
        """

        # STEP 1: Weekdays can not be an empty list
        weekdays = weekdays = self._get_weekdays()
        msg = '{method} requires at least one day of the week to check'
        assert weekdays, msg.format('_next_weekday')

        # STEP 2: Check if there is any valid day left in this week
        nextnatural = indate + timedelta(days=1)
        week_dates = self._get_week_dates(indate, 1, nextnatural)

        # STEP 3: If there is not any valid day left in this week
        # seach the first valid day in next week
        if not week_dates:
            nextmonday = indate + timedelta(days=7-indate.weekday())
            week_dates = self._get_week_dates(nextmonday, 1)

        # STEP 4: There will always be a valid day to return
        return week_dates[0]


    def _next_date(self, current_date):
        """ Computes next date, this will be the one that follows the given
        current_date. To do it, this method uses step of weekdays depending of
        the value chosen in rrule_type wizard field
        """

        computed_date = self._get_first_valid_date(current_date)

        if not computed_date > current_date:
            step = self._get_time_step()

            if self.rrule_type == 'weekly':
                computed_date = self._next_weekday(computed_date)
            elif self.rrule_type == 'monthly':
                computed_date = computed_date + step
                if self.month_by == 'day':
                    computed_date = self._get_month_nth_weekday(computed_date)
            else:
                computed_date = computed_date + step

        return computed_date


    def _complete_session(self, line, current_date, to_complete):
        """ Complete hours of the last session when it has not been filled
        with previous line

        @param line        : wizard line will be used to get required values
        @param current_date: date of the session will be complete
        @param to_complte  : maximun number of hours can be set to complete
        the session

        @return (integer): empty hours in session can be completed with the
        following line
        """

        msg = _(u'Could not remain more time %s than session length %s')
        if to_complete > self.duration:
            raise ValueError(msg % (to_complete, self.duration))

        start_time = self.start_time #self._get_start_time(line)
        start_time = start_time + self.duration - to_complete
        hours = min(line.maximum, to_complete)

        lesson = self._new_lesson(line, current_date, start_time, hours)
        self.training_lesson_ids = self.training_lesson_ids + lesson

        return to_complete - hours


    def _new_session(self, line, start_date=None, start_time=None, available=None):
        """ Creates new lesson and appends it to wizard.

        @param line      : wizard line to get values
        @param start_date: start date for lesson, keep empty to use from wizard
        @param start_time: start time for lesson, keep empty to use from wizard
        @param available : available hours can be used for lesson, keep empty
        to use full session time (line.duration)

        @return          : POSITIVE integer if there are available hours can be
        used to create new lessons, NEGATIVE integer if given availabel hours
        have not been enough to complete sesson, ZERO if lesson has complete
        session
        """
        if available:
            lesson = self._new_lesson(line, start_date, start_time, available)
            #lesson._onchange_training_action_id()
            lesson._onchange_training_module_id()

            self.training_lesson_ids = self.training_lesson_ids + lesson

            return available - self.duration

        return 0


    def _new_lesson(self, line, start_date=None, start_time=None, available=None):
        """ Creates new training lesson using given values and returns
        remaining hours in session

        @param line       : wizard line to get values
        @param start_date : start date for lesson, keep empty to use from wizard
        @param start_time : start time for lesson, keep empty to use from wizard
        @param available  : available hours can be used for lesson, keep empty
        to use full session time (line.duration)

        @return           : return value will be new created lesson
        """

        # STEP 1: Fill values if they have not been given
        start_date = fields.Date.from_string(self.start_date) \
            if start_date is None else start_date
        start_time = self.start_time if start_time is None else start_time
        available = line.duration if available is None else available

        # STEP 2: Lessons must have a duration greater than zero
        assert_msg = 'There are not enough ({hours}) hours for new lesson'
        assert available > 0, assert_msg.format(hours=available)

        # STEP 3: Lesson will occupy full session  if so has been indicated in
        # wizard line or if available (hours) value has not been set
        if line.incomplete == 'fill' or available is None:
            duration = line.duration
        else:
            duration = min(available, line.duration)

        # STEP 4: Build dictionary will be used to create lesson
        start_time = self._float_to_time(start_time)
        start_time = datetime.combine(start_date, start_time)
        values = dict(
            training_action_id=self.training_action_id.id,
            training_module_id=line.training_unit_id.id,
            description=None,
            active=True,
            start_date=fields.Datetime.to_string(start_time),
            duration=duration,
            teacher_id=line.teacher_id.id if line.teacher_id else None
        )

        # STEP 5: Create lesson and return it
        lesson_obj = self.env['academy.training.lesson']
        lesson_set = lesson_obj.create(values)

        return lesson_set


    # pylint: disable=locally-disabled, R0913
    def _process_line(self, line, last_date, to_complete):
        """ Proccess each line in wizard an creates needed sessions
        """

        # STEP 1: Complete last session if there are to_complete hours
        complete = to_complete
        if to_complete > 0:
            to_complete = self._complete_session( \
                line, last_date, to_complete)
            complete = complete - to_complete
            if to_complete >= 0:
                last_date = self._next_date(last_date)
            else:
                return last_date, abs(to_complete)

        # STEP 2: Get line variables
        start_time = self._get_start_time(line)
        first_date = self._get_start_date(line, last_date)
        hours = line.maximum - complete

        # STEP 3: Initialize the variables for loop
        first_date = self._get_first_valid_date(first_date)
        steps = ceil((line.maximum - to_complete) / line.duration)
        current_date = first_date
        session_date = current_date

        # STEP 5: Loop to create new sessions
        while steps > 0:

            if self.rrule_type == 'monthly' and self.month_by == 'day':
                steps = steps - 1
                session_date = self._get_month_nth_weekday(current_date)
                hours = self._new_session( \
                    line, session_date, start_time, hours)
                current_date = self._next_date(current_date)

            elif self.rrule_type == 'weekly':
                week_dates = self._get_week_dates( \
                    current_date, steps, first_date)

                for session_date in week_dates:
                    steps = steps - 1
                    hours = self._new_session( \
                        line, session_date, start_time, hours)

                current_date = self._next_date(session_date)

            else:
                steps = steps - 1
                session_date = current_date
                hours = self._new_session( \
                    line, session_date, start_time, hours)

                current_date = self._next_date(current_date)

        # STEP 6: Compute return values (tuple)
        # - If there are remaining hours, returned value will be a tuble with
        # last session date and remaining hours
        # - If rrule_type is weekly, next valid weekday will be computed and
        # returned
        # - Otherwise, date caused the loop exit will be returned, this is a
        # valid date for next line
        if hours != 0 and line.incomplete == 'next':
            return session_date, abs(min(0, hours))

        if self.rrule_type == 'weekly':
            return self._next_weekday(session_date), 0

        return current_date, 0

