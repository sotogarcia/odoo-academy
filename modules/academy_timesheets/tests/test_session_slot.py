# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.addons.academy_timesheets.lib.session_slot import SessionChain
from odoo.addons.academy_timesheets.lib.session_slot import SessionSlot

from logging import getLogger

from datetime import datetime, timedelta


_logger = getLogger(__name__)


class TestAcademyTestsSessionSlot(TransactionCase):

    def setUp(self):
        super(TestAcademyTestsSessionSlot, self).setUp()

        action_xid = 'academy_base.academy_training_action_demo_2'
        self._training_action = self.env.ref(action_xid)

        competency_xid = 'academy_base.academy_competency_unit_office'
        self._competency_unit = self.env.ref(competency_xid)

        self.date_base = datetime(year=2001, month=1, day=1)

        self._session_obj = self.env['academy.training.session']

        # Log a sample of each representation string
        self._debug_repr()

    def _create_session(self, date_start, date_stop, validate=True):
        values = {
            'description': None,
            'active': True,
            'state': 'ready',
            'training_action_id': self._training_action.id,
            'competency_unit_id': self._competency_unit.id,
            'date_start': date_start,
            'date_stop': date_stop,
            'validate': validate,
        }
        return self._session_obj.create(values)

    @staticmethod
    def _move_session(session, days=0, seconds=0, microseconds=0,
                      milliseconds=0, minutes=0, hours=0, weeks=0):

        date_start = session.date_start + \
            timedelta(days, seconds, microseconds, milliseconds, minutes,
                      hours, weeks)

        date_stop = session.date_stop + \
            timedelta(days, seconds, microseconds, milliseconds, minutes,
                      hours, weeks)

        session.write({
            'date_start': date_start.strftime('%Y-%m-%d %H:%M:%S'),
            'date_stop': date_stop.strftime('%Y-%m-%d %H:%M:%S')
        })

    def _create_session_gamut(self):
        """           A              B
                      |---- SLOT ----|

            |-O1-| |-V1-|  |-I2-|  |-V2-| |-O2-|
            C    D E    F  G    H  I    J K    L

                 |-A1-|-I1-|    |-I3-|-A2-|
                 D    A    G    H    B    K

            On => Out of slot
            Vn => oVerlapping the slot
            In => Inside the slot
            An => Adjacent to the slot
        """

        gamut = {}

        # 10:00 - 12:00 / Slot bounds
        a = self.date_base.replace(hour=10)
        b = self.date_base.replace(hour=12)
        slot = SessionSlot(self.env, a, b)

        # 8:00 - 9:00
        c = self.date_base.replace(hour=8)
        d = self.date_base.replace(hour=9)
        gamut['o1'] = self._create_session(c, d)

        # 9:15 - 10:15
        e = self.date_base.replace(hour=9, minute=15)
        f = self.date_base.replace(hour=10, minute=15)
        gamut['v1'] = self._create_session(e, f)

        # 10:30 - 11:30
        g = self.date_base.replace(hour=10, minute=30)
        h = self.date_base.replace(hour=11, minute=30)
        gamut['i2'] = self._create_session(g, h)

        # 11:45 - 12:45
        i = self.date_base.replace(hour=11, minute=45)
        j = self.date_base.replace(hour=12, minute=45)
        gamut['v2'] = self._create_session(i, j)

        # 13:00 - 14:00
        k = self.date_base.replace(hour=13)
        ll = self.date_base.replace(hour=14)
        gamut['o2'] = self._create_session(k, ll)

        # 9:00 - 10:00
        gamut['a1'] = self._create_session(d, a, validate=False)

        # 10:00 - 10:30
        gamut['i1'] = self._create_session(a, g, validate=False)

        # 11:30 - 12:00
        gamut['i3'] = self._create_session(h, b, validate=False)

        # 12:00 - 13:00
        gamut['a2'] = self._create_session(b, k, validate=False)

        return slot, gamut

    @staticmethod
    def _unlink_session_gamut(gamut):
        for k, v in gamut.items():
            v.unlink()

    def _debug_repr(self):
        """ Send to the log a sample of each object representation __repr__
        """

        slot, sessions = self._create_session_gamut()

        slot.register(sessions['i2'])

        slot_repr = 'Slot.__repr__: {}'.format(slot)
        _logger.debug(slot_repr)

        piece_repr = 'Piece.__repr__: {}'.format(slot._pieces[0])
        _logger.debug(piece_repr)

        self._unlink_session_gamut(sessions)

    def test_slot_create(self):
        """ On create, date_stop must be greater than date_start
        """

        a = self.date_base.replace(hour=10)
        b = self.date_base.replace(hour=12)
        try:
            SessionSlot(self.env, a, b)
        except ValidationError as ve:
            self.fail(ve)

        a = self.date_base.replace(hour=12)
        b = self.date_base.replace(hour=10)
        with self.assertRaises(ValidationError):
            SessionSlot(self.env, a, b)

        a = self.date_base.replace(hour=10)
        b = self.date_base.replace(hour=10)
        with self.assertRaises(ValidationError):
            SessionSlot(self.env, a, b)

    def test_slot_is_out(self):
        """         A           B
                    |--- SLOT---|
            |---| |---| |---| |---| |---|
            C   D E   F G   H I   J K   L
                |---|---|   |---|---|
                D   A   G   H   B   K
        """

        slot, sessions = self._create_session_gamut()

        # 8:00 - 9:00
        self.assertTrue(
            slot.is_out(sessions['o1']), 'test_is_out: Out to the left')

        # 9:00 - 10:00
        self.assertTrue(
            slot.is_out(sessions['a1']), 'test_is_out: Adjacent on the left')

        # 9:15 - 10:15
        self.assertFalse(
            slot.is_out(sessions['v1']), 'test_is_out: Left overlapping')

        # 10:00 - 10:30
        self.assertFalse(
            slot.is_out(sessions['i1']), 'test_is_out: Inside')

        # 10:30 - 11:30
        self.assertFalse(
            slot.is_out(sessions['i2']), 'test_is_out: Inside')

        # 11:30 - 12:00
        self.assertFalse(
            slot.is_out(sessions['i3']), 'test_is_out: Inside')

        # 11:45 - 12:45
        self.assertFalse(
            slot.is_out(sessions['v2']), 'test_is_out: Right overlapping')

        # 12:00 - 13:00
        self.assertTrue(
            slot.is_out(sessions['a2']), 'test_is_out: Adjacent on the rigth')

        # 13:00 - 14:00
        self.assertTrue(
            slot.is_out(sessions['o2']), 'test_is_out: Out to the right')

        self._unlink_session_gamut(sessions)

    def test_slot_register(self):
        # 8:00 - 9:00

        slot, sessions = self._create_session_gamut()

        # 8:00 - 9:00
        slot.register(sessions['o1'])
        self.assertEqual(slot.length, 0, 'test_register: Out to the left')

        # 9:00 - 10:00
        slot.register(sessions['a1'])
        self.assertEqual(slot.length, 0, 'test_register: Adjacent on the left')

        # 9:15 - 10:15
        slot.register(sessions['v1'])
        self.assertEqual(slot.length, 1, 'test_register: Left overlapping')
        self.assertEqual(slot._pieces[0].date_start, slot.date_start,
                         'test_register: Left overlapping')

        # 10:00 - 10:30
        slot.register(sessions['i1'])
        self.assertEqual(slot.length, 2, 'test_register: Inside')

        # 10:30 - 11:30
        slot.register(sessions['i2'])
        self.assertEqual(slot.length, 3, 'test_register: Inside')

        # 11:30 - 12:00
        slot.register(sessions['i3'])
        self.assertEqual(slot.length, 4, 'test_register: Inside')

        # 11:45 - 12:45
        slot.register(sessions['v2'])
        self.assertEqual(slot.length, 5, 'test_register: Right overlapping')
        self.assertEqual(slot._pieces[-1].date_stop, slot.date_stop,
                         'test_register: Right overlapping')

        # 12:00 - 13:00
        slot.register(sessions['a2'])
        self.assertEqual(slot.length, 5, 'test_register: Adjacent at rigth')

        # 13:00 - 14:00
        slot.register(sessions['o2'])
        self.assertEqual(slot.length, 5, 'test_register: Out to the right')

        session_set = self.env['academy.training.session']
        for k, v in sessions.items():
            session_set += v

        a = self.date_base.replace(hour=10)
        b = self.date_base.replace(hour=12)
        slot = SessionSlot(self.env, a, b)

        slot.register(session_set)
        self.assertEqual(slot.length, 5, 'test_register: multiple records')

        self.assertEqual(slot._pieces[0].date_start, slot.date_start,
                         'test_register: Left overlapping')
        self.assertEqual(slot._pieces[-1].date_stop, slot.date_stop,
                         'test_register: Right overlapping')

        self._unlink_session_gamut(sessions)

    def test_slot_move(self):
        slot, sessions = self._create_session_gamut()

        for k, v in sessions.items():
            slot.register(v)

        offset = timedelta(days=1, hours=1, minutes=30)
        slot.move(slot.date_start + offset)
        slot.save()

        # 10:00 - 12:00 / Slot bounds
        a = self.date_base.replace(hour=10)
        b = self.date_base.replace(hour=12)

        # 8:00 - 9:00
        c = self.date_base.replace(hour=8)
        d = self.date_base.replace(hour=9)
        self.assertEqual(sessions['o1'].date_start, c,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['o1'].date_stop, d,
                         msg='test_slot_move: out session 1')

        # 9:15 - 10:15
        # e = self.date_base.replace(hour=9, minute=15)
        # Session will be resized
        f = self.date_base.replace(hour=10, minute=15)
        self.assertEqual(sessions['v1'].date_start, a + offset,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['v1'].date_stop, f + offset,
                         msg='test_slot_move: out session 1')

        # 10:30 - 11:30
        g = self.date_base.replace(hour=10, minute=30)
        h = self.date_base.replace(hour=11, minute=30)
        self.assertEqual(sessions['i2'].date_start, g + offset,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['i2'].date_stop, h + offset,
                         msg='test_slot_move: out session 1')

        # 11:45 - 12:45
        i = self.date_base.replace(hour=11, minute=45)
        # j = self.date_base.replace(hour=12, minute=45)
        # Session will be resized
        self.assertEqual(sessions['v2'].date_start, i + offset,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['v2'].date_stop, b + offset,
                         msg='test_slot_move: out session 1')

        # 13:00 - 14:00
        k = self.date_base.replace(hour=13)
        ll = self.date_base.replace(hour=14)
        self.assertEqual(sessions['o2'].date_start, k,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['o2'].date_stop, ll,
                         msg='test_slot_move: out session 1')

        # 9:00 - 10:00
        self.assertEqual(sessions['a1'].date_start, d,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['a1'].date_stop, a,
                         msg='test_slot_move: out session 1')

        # 10:00 - 10:30
        self.assertEqual(sessions['i1'].date_start, a + offset,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['i1'].date_stop, g + offset,
                         msg='test_slot_move: out session 1')

        # 11:30 - 12:00
        self.assertEqual(sessions['i3'].date_start, h + offset,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['i3'].date_stop, b + offset,
                         msg='test_slot_move: out session 1')

        # 12:00 - 13:00
        self.assertEqual(sessions['a2'].date_start, b,
                         msg='test_slot_move: out session 1')
        self.assertEqual(sessions['a2'].date_stop, k,
                         msg='test_slot_move: out session 1')

        self._unlink_session_gamut(sessions)

    def test_chain_create(self):
        slot, sessions = self._create_session_gamut()

        # Monday
        monday = self.date_base
        # Stay sessions['v1']
        # Stay sesssion['o1']

        # Tuesday (no slot)
        # tuesday = self.date_base + timedelta(days=1)
        self._move_session(sessions['i1'], days=1)

        # Wednesday
        wednesday = self.date_base + timedelta(days=2)
        self._move_session(sessions['a1'], days=2)
        self._move_session(sessions['i2'], days=2)
        self._move_session(sessions['a2'], days=2)

        # Thursday (no slot)
        # thursday = self.date_base + timedelta(days=1)
        self._move_session(sessions['i3'], days=3)

        # Friday
        friday = self.date_base + timedelta(days=4)
        self._move_session(sessions['v2'], days=4)
        self._move_session(sessions['o2'], days=4)

        chain = SessionChain(self.env, self._training_action)
        chain.append(friday.replace(hour=10), friday.replace(hour=12))
        chain.append(monday.replace(hour=10), monday.replace(hour=12))
        chain.append(wednesday.replace(hour=10), wednesday.replace(hour=12))

        self.assertEqual(chain._slots[0].date_start, monday.replace(hour=10),
                         'test_chain_create: monday slot')
        self.assertEqual(chain._slots[1].date_stop,
                         (wednesday + timedelta(hours=2)).replace(hour=12),
                         'test_chain_create: wednesday slot')
        self.assertEqual(chain._slots[-1].date_start, friday.replace(hour=10),
                         'test_chain_create: friday slot')

        self.assertEqual(chain._slots[0].length, 1,
                         'test_chain_create: monday slot sessions')
        self.assertEqual(chain._slots[1].length, 1,
                         'test_chain_create: wednesday slot sessions')
        self.assertEqual(chain._slots[2].length, 1,
                         'test_chain_create: friday slot sessions')

        self._unlink_session_gamut(sessions)
