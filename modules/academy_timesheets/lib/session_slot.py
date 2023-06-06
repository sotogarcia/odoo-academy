# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta, time, date

from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _


class SessionChain:

    def __init__(self, environment, training_action):
        self._env = environment
        self._slots = []
        self._index = 0

        if isinstance(training_action, int):
            training_action_obj = self.env['academy.training.action']
            training_action = training_action_obj.browse(training_action)

        self._training_action = training_action
        self._load_sessions()
        self._compute_time()

    def _compute_time(self):
        self._cu_time = {}
        for unit in self.competencies:
            self._cu_time[unit.id] = (unit.hours - unit.schedule)

    def _load_sessions(self):
        training_action_id = self._training_action.id
        session_domain = [('training_action_id', '=', training_action_id)]
        session_obj = self._env['academy.training.session']
        self._session_set = session_obj.search(session_domain)

    @property
    def competencies(self):
        return self._training_action.competency_unit_ids

    @property
    def sessions(self):
        return self._session_set

    def append(self, date_start, date_stop, fill=True):
        slot = SessionSlot(self._env, date_start, date_stop)
        slot.register(self._session_set)
        slot.fill(self._cu_time)
        self._slots.append(slot)
        self._slots.sort(key=lambda s: s.date_start)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self._slots):
            self._index += 1
            return self._slots[self._index - 1]
        else:
            raise StopIteration


class SessionSlot:

    def __init__(self, environment, date_start, date_stop):

        self._env = environment
        self._index = 0

        self._date_start = date_start
        self._date_stop = date_stop

        if date_stop <= date_start:
            msg = _('Slot cannot end ({}) before starting ({})')
            date_start = self._date_start.strftime('%x %X')
            date_stop = self._date_stop.strftime('%x %X')
            raise ValidationError(msg.format(date_start, date_stop))

        self._pieces = []

    @property
    def date_start(self):
        return self._date_start

    @property
    def date_stop(self):
        return self._date_stop

    @property
    def date_delay(self):
        return (self._date_stop - self._date_start).total_seconds() / 3600

    @property
    def length(self):
        return len(self._pieces)

    def is_out(self, session):
        above = session.date_start >= self._date_stop
        below = session.date_stop <= self._date_start

        return above or below

    def empty(self):
        self._pieces = []

    def register(self, session_set):
        for session in session_set:
            if self.is_out(session):
                continue

            date_start = max(self._date_start, session.date_start)
            date_stop = min(self._date_stop, session.date_stop)
            piece = SessionPiece(self._env, date_start, date_stop, session)
            self._pieces.append(piece)

        self._pieces.sort(key=lambda p: (p.date_start, p.date_stop))

    def fill(self, cu_time):
        env = self._env

        for available in self.available:

            free_start, free_stop = available[0], available[1]
            start = free_start
            while start < free_stop:

                unit_id, untaught = self._next_available(cu_time)
                if not (unit_id and untaught):
                    msg = _('There are not enough competency units')
                    raise UserError(msg)

                delay = self._float_interval(start, free_stop)
                delay = min(delay, untaught)
                stop = self._date_addition(start, delay)

                piece = SessionPiece(env, start, stop, competency=unit_id)
                self._pieces.append(piece)

                cu_time[unit_id] -= delay
                start = stop

    def move(self, date_start):

        try:
            offset = date_start - self._date_start
            self._date_start = date_start
            self._date_stop += offset

            for piece in self._pieces:
                piece.move(offset)

        except Exception as ex:
            msg = _('It is not possible to move the sessions between {} and '
                    '{}, to place them starting from {}. System says: «{}»')
            msg.format(
                self._date_start.strftime('%c'),
                self._date_stop.strftime('%c'),
                date_start.strftime('%c'),
                ex
            )
            raise UserError(msg)

    def resize(self):
        pass

    def save(self):
        for piece in self._pieces:
            piece.save()

    @property
    def available(self):
        pairs = []
        top = self._date_start

        if not self._pieces:
            pair = (self._date_start, self._date_stop)
            pairs.append(pair)
            top = pair[1]

        else:

            if self._date_start < self._pieces[0].date_start:
                pair = (self._date_start, self._pieces[0].date_start)
                pairs.append(pair)
                top = pair[1]

            for piece in self._pieces:
                if piece.date_start > top:
                    pair = (top, piece.date_start)
                    pairs.append(pair)
                    top = pair[1]
                elif piece.date_stop > top:
                    top = piece.date_stop

                if top >= self._date_stop:
                    break

            if top < self._date_stop:
                pair = (top, self._date_stop)
                pairs.append(pair)
                top = self._date_stop

        return pairs

    @staticmethod
    def _date_addition(dt, hours):
        """  Sum the given time, in hours, to the given datetime value.

        Args:
            dt (datetime): base date/time value or date value instead
            hours (float): time offset given in hours
        """

        if type(dt) is date: # noqa: E721
            dt = datetime.combine(dt, time.min)

        return dt + timedelta(hours=hours)

    @staticmethod
    def _float_interval(date_start, date_stop, natural=True):
        difference = date_stop - date_start
        difference = difference.total_seconds()

        if natural:
            value = max(difference, 0)

        return value / 3600.0

    def _next_available(self, cu_time):
        competency_unit_id, untaught = None, None

        for k, v in cu_time.items():
            if v > 0:
                competency_unit_id, untaught = k, v
                break

        return competency_unit_id, untaught

    @staticmethod
    def _piece_repr(td, cuid=None):
        minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
        hours, minutes = divmod(minutes, 60)

        tp = '{hs:d}:{ms:02d}:{ss:02d}' if seconds else '{hs:d}:{ms:02d}'
        tm = tp.format(hs=hours, ms=minutes, ss=seconds)

        return '{} ({})'.format(tm, cuid or '#')

    def __repr__(self):

        if self._pieces:
            items = []
            top = self._date_start
            for piece in self._pieces:
                if piece.date_start > top:
                    td = piece.date_start - top
                    item = self._piece_repr(td, None)
                    items.append(item)

                td = piece.date_stop - piece.date_start
                item = self._piece_repr(td, piece.competency.id)
                items.append(item)

                top = piece._date_stop

            if top < self._date_stop:
                td = self._date_stop - top
                item = self._piece_repr(td, None)
                items.append(item)

            items = ', '.join(items)
        else:
            items = _('Empty')

        return 'SessionSlot({}: {})'.format(self._date_start, items)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self._pieces):
            self._index += 1
            return self._pieces[self._index - 1]
        else:
            raise StopIteration


class SessionPiece:

    def __init__(self, env, date_start, date_stop, session=None,
                 competency=None):

        self._date_start = date_start
        self._date_stop = date_stop

        if date_stop <= date_start:
            msg = _('Piece cannot end ({}) before starting ({})')
            date_start = self._date_start.strftime('%x %X')
            date_stop = self._date_stop.strftime('%x %X')
            raise ValidationError(msg.format(date_start, date_stop))

        self._env = env

        if isinstance(session, int):
            session_obj = self._env['academy.training.session']
            if session > 0:
                self._session = session_obj.browse(session)
            else:
                self._sessoin = session_obj
        else:
            self._session = session

        if not competency and self._session:
            self._competency_unit = self._session.competency_unit_id
        else:
            if isinstance(competency, int):
                competency_obj = self._env['academy.competency.unit']
                self._competency_unit = competency_obj.browse(competency)
            else:
                self._competency_unit = competency

        try:
            self._competency_unit.ensure_one()
        except Exception as ex:
            msg = _('Piece must have a valid competency unit. ({})')
            raise ValidationError(msg.format(ex))

    @property
    def date_start(self):
        return self._date_start

    @property
    def date_stop(self):
        return self._date_stop

    @property
    def date_delay(self):
        return (self._date_stop - self._date_start).total_seconds() / 3600

    @property
    def session(self):
        return self._session

    @property
    def competency(self):
        return self._competency_unit

    def move(self, offset):
        self._date_start = self._date_start + offset
        self._date_stop = self._date_stop + offset

        if self._date_stop <= self._date_start:
            msg = _('Piece cannot end ({}) before starting ({})')
            date_start = self._date_start.strftime('%x %X')
            date_stop = self._date_stop.strftime('%x %X')
            raise ValidationError(msg.format(date_start, date_stop))

    def save(self, values=None):
        values = values or {}
        values.update({
            'date_start': self._date_start,
            'date_stop': self._date_stop,
            'competency_unit_id': self._competency_unit.id
        })

        if self._session:
            if self._needs_update():
                self._session.write(values)
        else:
            session_obj = self._env['academy.training.session']
            self._session = session_obj.create(values)

    def _needs_update(self):
        result = False

        if bool(self._session):
            cu_changed = \
                self._session.competency_unit_id.id != self._competency_unit.id
            date_start_changed = self._session.date_start != self.date_start
            date_stop_changed = self._session.date_start != self.date_start

            result = cu_changed or date_start_changed or date_stop_changed

    def __repr__(self):
        delay = timedelta(hours=self.date_delay)

        minutes, seconds = divmod(delay.seconds + delay.days * 86400, 60)
        hours, minutes = divmod(minutes, 60)

        tp = '{hs:d}:{ms:02d}:{ss:02d}' if seconds else '{hs:d}:{ms:02d}'
        tm = tp.format(hs=hours, ms=minutes, ss=seconds)

        cuid = self._competency_unit.id

        return 'SessionPiece({}: {} ({}))'.format(self._date_start, tm, cuid)
