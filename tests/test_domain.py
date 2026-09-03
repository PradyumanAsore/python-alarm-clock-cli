"""
Unit tests for the Alarm Clock domain layer.
"""

import unittest
from datetime import datetime, timedelta, timezone, time
from alarm_clock.domain import (
    Alarm,
    AlarmStatus,
    RecurringMode,
    parse_alarm_time
)


class TestAlarmDomain(unittest.TestCase):
    def setUp(self):
        self.tz = timezone.utc
        self.now = datetime(2026, 9, 3, 12, 0, 0, tzinfo=self.tz)

    def test_alarm_initialization(self):
        alarm = Alarm(id=1, target_time=self.now, label="Test Alarm")
        self.assertEqual(alarm.id, 1)
        self.assertEqual(alarm.target_time, self.now)
        self.assertEqual(alarm.label, "Test Alarm")
        self.assertEqual(alarm.status, AlarmStatus.PENDING)
        self.assertEqual(alarm.effective_time, self.now)

    def test_alarm_naive_datetime_raises_error(self):
        naive_dt = datetime(2026, 9, 3, 12, 0, 0)
        with self.assertRaises(ValueError):
            Alarm(id=1, target_time=naive_dt)

    def test_is_due_and_trigger(self):
        future_time = self.now + timedelta(minutes=10)
        alarm = Alarm(id=1, target_time=future_time)

        # Before time
        self.assertFalse(alarm.is_due(self.now))
        self.assertFalse(alarm.trigger(self.now))
        self.assertEqual(alarm.status, AlarmStatus.PENDING)

        # At time
        self.assertTrue(alarm.is_due(future_time))
        self.assertTrue(alarm.trigger(future_time))
        self.assertEqual(alarm.status, AlarmStatus.TRIGGERED)

        # Once triggered, not due again until snoozed/reset
        self.assertFalse(alarm.is_due(future_time + timedelta(seconds=1)))

    def test_snooze_behavior(self):
        alarm = Alarm(id=1, target_time=self.now)
        alarm.trigger(self.now)

        snooze_until = alarm.snooze(current_time=self.now, minutes=5)
        expected_snooze = self.now + timedelta(minutes=5)

        self.assertEqual(snooze_until, expected_snooze)
        self.assertEqual(alarm.status, AlarmStatus.SNOOZED)
        self.assertEqual(alarm.effective_time, expected_snooze)

        # Check due status when snoozed
        self.assertFalse(alarm.is_due(self.now + timedelta(minutes=2)))
        self.assertTrue(alarm.is_due(expected_snooze))

    def test_snooze_invalid_minutes(self):
        alarm = Alarm(id=1, target_time=self.now)
        with self.assertRaises(ValueError):
            alarm.snooze(self.now, minutes=0)

    def test_snooze_cancelled_alarm_raises_error(self):
        alarm = Alarm(id=1, target_time=self.now)
        alarm.cancel()
        with self.assertRaises(ValueError):
            alarm.snooze(self.now, minutes=5)

    def test_dismiss_one_time_alarm(self):
        alarm = Alarm(id=1, target_time=self.now)
        alarm.trigger(self.now)

        next_occ = alarm.dismiss()
        self.assertIsNone(next_occ)
        self.assertEqual(alarm.status, AlarmStatus.DISMISSED)

    def test_dismiss_recurring_daily_alarm(self):
        alarm = Alarm(
            id=1,
            target_time=self.now,
            recurring=RecurringMode.DAILY
        )
        alarm.trigger(self.now)

        next_occ = alarm.dismiss()
        expected_next = self.now + timedelta(days=1)
        self.assertEqual(next_occ, expected_next)
        self.assertEqual(alarm.target_time, expected_next)
        self.assertEqual(alarm.status, AlarmStatus.PENDING)

    def test_dismiss_recurring_weekdays_alarm(self):
        # 2026-09-04 is Friday
        friday = datetime(2026, 9, 4, 12, 0, 0, tzinfo=self.tz)
        alarm = Alarm(
            id=1,
            target_time=friday,
            recurring=RecurringMode.WEEKDAYS
        )

        next_occ = alarm.dismiss()
        # Friday + 1 day = Saturday, skipping to Monday 2026-09-07
        monday = datetime(2026, 9, 7, 12, 0, 0, tzinfo=self.tz)
        self.assertEqual(next_occ, monday)

    def test_parse_alarm_time_relative(self):
        dt = parse_alarm_time("+15m", relative_to=self.now)
        self.assertEqual(dt, self.now + timedelta(minutes=15))

        dt_sec = parse_alarm_time("+30s", relative_to=self.now)
        self.assertEqual(dt_sec, self.now + timedelta(seconds=30))

        dt_hr = parse_alarm_time("+2h", relative_to=self.now)
        self.assertEqual(dt_hr, self.now + timedelta(hours=2))

    def test_parse_alarm_time_wall_clock_future_today(self):
        # Current time is 12:00, parse 14:30
        dt = parse_alarm_time("14:30", relative_to=self.now)
        expected = datetime(2026, 9, 3, 14, 30, 0, tzinfo=self.tz)
        self.assertEqual(dt, expected)

    def test_parse_alarm_time_wall_clock_past_today_advances_to_tomorrow(self):
        # Current time is 12:00, parse 08:30 (already passed today)
        dt = parse_alarm_time("08:30", relative_to=self.now)
        expected = datetime(2026, 9, 4, 8, 30, 0, tzinfo=self.tz)
        self.assertEqual(dt, expected)

    def test_parse_alarm_time_invalid_format(self):
        with self.assertRaises(ValueError):
            parse_alarm_time("invalid_time", relative_to=self.now)
        with self.assertRaises(ValueError):
            parse_alarm_time("+10x", relative_to=self.now)


if __name__ == "__main__":
    unittest.main()
