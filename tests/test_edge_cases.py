"""
Comprehensive edge case tests for Alarm Clock CLI.
"""

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from alarm_clock.clock import TestClock
from alarm_clock.domain import AlarmStatus, RecurringMode, parse_alarm_time
from alarm_clock.cli import CommandParser
from alarm_clock.notifier import TestNotifier
from alarm_clock.service import AlarmService


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.tz = timezone.utc
        self.start_time = datetime(2026, 9, 3, 23, 58, 0, tzinfo=self.tz)
        self.clock = TestClock(self.start_time)
        self.notifier = TestNotifier()
        self.service = AlarmService(clock=self.clock, notifier=self.notifier)
        self.parser = CommandParser(self.service)

    def test_system_sleep_clock_jump_triggers_missed_alarms(self):
        async def run_test():
            alarm1 = self.service.add_alarm("+5m", label="Alarm 1")
            alarm2 = self.service.add_alarm("+10m", label="Alarm 2")

            # Simulate system sleep: clock jumps forward by 2 hours
            self.clock.advance(timedelta(hours=2))

            # Ticker runs after waking up
            triggered = await self.service.tick()
            self.assertEqual(len(triggered), 2)
            self.assertEqual(len(self.notifier.notifications), 2)
            self.assertEqual(alarm1.status, AlarmStatus.TRIGGERED)
            self.assertEqual(alarm2.status, AlarmStatus.TRIGGERED)

        asyncio.run(run_test())

    def test_stress_multiple_simultaneous_alarms(self):
        async def run_test():
            alarms = [self.service.add_alarm("+10s", label=f"Batch {i}") for i in range(10)]
            self.clock.advance(10.0)

            triggered = await self.service.tick()
            self.assertEqual(len(triggered), 10)
            self.assertEqual(len(self.notifier.notifications), 10)

        asyncio.run(run_test())

    def test_re_snooze_snoozed_alarm(self):
        async def run_test():
            alarm = self.service.add_alarm("+10s", label="Re-snooze test")
            self.clock.advance(10.0)
            await self.service.tick()

            # First snooze: +5m
            self.service.snooze_alarm(alarm.id, minutes=5)
            first_snooze = alarm.effective_time

            # Second snooze: +10m from current time
            self.clock.advance(timedelta(minutes=1))
            self.service.snooze_alarm(alarm.id, minutes=10)
            second_snooze = alarm.effective_time

            self.assertGreater(second_snooze, first_snooze)
            self.assertEqual(second_snooze, self.clock.now() + timedelta(minutes=10))

        asyncio.run(run_test())

    def test_midnight_rollover_parse(self):
        # Current time 23:58. Parse 00:05 (5 minutes after midnight)
        dt = parse_alarm_time("00:05", relative_to=self.start_time)
        # Should be scheduled for tomorrow (2026-09-04 00:05:00)
        expected = datetime(2026, 9, 4, 0, 5, 0, tzinfo=self.tz)
        self.assertEqual(dt, expected)

    def test_invalid_quoted_string_handling(self):
        # Unclosed quote string
        res = self.parser.execute("add +10m \"Unclosed quote")
        self.assertIn("[-] Command parse error:", res)

    def test_invalid_id_format_handling(self):
        res = self.parser.execute("snooze abc 10")
        self.assertIn("[-] Error:", res)

        res_cancel = self.parser.execute("cancel xyz")
        self.assertIn("[-] Error:", res_cancel)

        res_dismiss = self.parser.execute("dismiss foo")
        self.assertIn("[-] Error:", res_dismiss)


if __name__ == "__main__":
    unittest.main()
