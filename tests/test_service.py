"""
Unit tests for AlarmService using TestClock and TestNotifier.
"""

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from alarm_clock.clock import TestClock
from alarm_clock.domain import AlarmStatus, RecurringMode
from alarm_clock.notifier import TestNotifier
from alarm_clock.service import AlarmService


class TestAlarmService(unittest.TestCase):
    def setUp(self):
        self.tz = timezone.utc
        self.start_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=self.tz)
        self.clock = TestClock(self.start_time)
        self.notifier = TestNotifier()
        self.service = AlarmService(clock=self.clock, notifier=self.notifier)

    def test_add_and_list_alarm(self):
        alarm = self.service.add_alarm("+10m", label="Meeting")
        self.assertEqual(alarm.id, 1)
        self.assertEqual(alarm.label, "Meeting")
        self.assertEqual(alarm.target_time, self.start_time + timedelta(minutes=10))

        alarms = self.service.list_alarms()
        self.assertEqual(len(alarms), 1)
        self.assertEqual(alarms[0].id, 1)

    def test_get_nonexistent_alarm_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.service.get_alarm(999)

    def test_cancel_alarm(self):
        alarm = self.service.add_alarm("+10m", label="Test")
        self.service.cancel_alarm(alarm.id)
        self.assertEqual(alarm.status, AlarmStatus.CANCELLED)

    def test_single_tick_triggers_due_alarm(self):
        async def run_test():
            alarm = self.service.add_alarm("+10s", label="Fast alarm")
            
            # Initial tick before time
            triggered = await self.service.tick()
            self.assertEqual(len(triggered), 0)
            self.assertEqual(len(self.notifier.notifications), 0)

            # Advance clock past alarm time
            self.clock.advance(15.0)
            triggered = await self.service.tick()
            self.assertEqual(len(triggered), 1)
            self.assertEqual(triggered[0].id, alarm.id)
            self.assertEqual(len(self.notifier.notifications), 1)
            self.assertEqual(self.notifier.notifications[0].id, alarm.id)

        asyncio.run(run_test())

    def test_multiple_simultaneous_alarms_trigger(self):
        async def run_test():
            alarm1 = self.service.add_alarm("+10s", label="Alarm 1")
            alarm2 = self.service.add_alarm("+10s", label="Alarm 2")

            self.clock.advance(10.0)
            triggered = await self.service.tick()

            self.assertEqual(len(triggered), 2)
            self.assertEqual(len(self.notifier.notifications), 2)

        asyncio.run(run_test())

    def test_snooze_and_retrigger(self):
        async def run_test():
            alarm = self.service.add_alarm("+10s", label="Snooze test")
            self.clock.advance(10.0)
            await self.service.tick()
            self.assertEqual(alarm.status, AlarmStatus.TRIGGERED)

            # Snooze for 5 minutes
            self.service.snooze_alarm(alarm.id, minutes=5)
            self.assertEqual(alarm.status, AlarmStatus.SNOOZED)

            # Tick before snooze time
            self.clock.advance(timedelta(minutes=2))
            triggered = await self.service.tick()
            self.assertEqual(len(triggered), 0)

            # Advance past snooze time
            self.clock.advance(timedelta(minutes=4))
            triggered = await self.service.tick()
            self.assertEqual(len(triggered), 1)
            self.assertEqual(triggered[0].id, alarm.id)

        asyncio.run(run_test())

    def test_recurring_alarm_dismiss_replaces_target_time(self):
        async def run_test():
            alarm = self.service.add_alarm(
                "+10s",
                label="Daily check",
                recurring=RecurringMode.DAILY
            )
            self.clock.advance(10.0)
            await self.service.tick()

            # Dismiss recurring alarm
            self.service.dismiss_alarm(alarm.id)
            self.assertEqual(alarm.status, AlarmStatus.PENDING)
            self.assertEqual(
                alarm.target_time,
                self.start_time + timedelta(seconds=10) + timedelta(days=1)
            )

        asyncio.run(run_test())

    def test_run_loop_termination(self):
        async def run_test():
            stop_event = asyncio.Event()
            alarm = self.service.add_alarm("+2s", label="Loop test")

            # Start run_loop in background task
            loop_task = asyncio.create_task(self.service.run_loop(stop_event))

            # Wait a tick then set stop_event
            await asyncio.sleep(0.01)
            stop_event.set()
            await loop_task

            # Clock advanced via simulated sleep in loop
            self.assertGreater(self.clock.now(), self.start_time)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
