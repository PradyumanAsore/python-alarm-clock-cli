"""
Unit tests for CLI parser and command execution.
"""

import unittest
from datetime import datetime, timezone
from alarm_clock.clock import TestClock
from alarm_clock.cli import CommandParser, format_alarm_table, format_help
from alarm_clock.notifier import TestNotifier
from alarm_clock.service import AlarmService


class TestCLIController(unittest.TestCase):
    def setUp(self):
        self.tz = timezone.utc
        self.start_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=self.tz)
        self.clock = TestClock(self.start_time)
        self.notifier = TestNotifier()
        self.service = AlarmService(clock=self.clock, notifier=self.notifier)
        self.parser = CommandParser(self.service)

    def test_help_command(self):
        res = self.parser.execute("help")
        self.assertIn("Available Commands:", res)

    def test_exit_command(self):
        self.assertEqual(self.parser.execute("exit"), "EXIT")
        self.assertEqual(self.parser.execute("quit"), "EXIT")

    def test_empty_input(self):
        self.assertEqual(self.parser.execute("   "), "")

    def test_add_command(self):
        res = self.parser.execute("add +10m Test alarm")
        self.assertIn("[+] Alarm #1 created", res)

        alarms = self.service.list_alarms()
        self.assertEqual(len(alarms), 1)
        self.assertEqual(alarms[0].label, "Test alarm")

    def test_add_command_with_recurring_flag(self):
        res = self.parser.execute("add 08:00 Work wake --weekdays")
        self.assertIn("(weekdays)", res)

        alarms = self.service.list_alarms()
        self.assertEqual(alarms[0].label, "Work wake")

    def test_add_command_invalid_syntax(self):
        res = self.parser.execute("add")
        self.assertIn("[-] Usage:", res)

        res_err = self.parser.execute("add invalid_time")
        self.assertIn("[-] Error:", res_err)

    def test_list_command_empty_and_populated(self):
        res_empty = self.parser.execute("list")
        self.assertEqual(res_empty, "No alarms scheduled.")

        self.parser.execute("add +5m First")
        res_list = self.parser.execute("list")
        self.assertIn("First", res_list)
        self.assertIn("PENDING", res_list)

    def test_snooze_command(self):
        self.parser.execute("add +5s Alarm")
        self.clock.advance(5.0)

        # Execute snooze
        res = self.parser.execute("snooze 1 10")
        self.assertIn("[zZz] Alarm #1 snoozed", res)

        alarm = self.service.get_alarm(1)
        self.assertEqual(alarm.status.name, "SNOOZED")

    def test_snooze_invalid_id(self):
        res = self.parser.execute("snooze 99")
        self.assertIn("[-] Error:", res)

    def test_dismiss_command(self):
        self.parser.execute("add +5s Alarm")
        res = self.parser.execute("dismiss 1")
        self.assertIn("[x] Alarm #1 dismissed", res)

    def test_cancel_command(self):
        self.parser.execute("add +5m Alarm")
        res = self.parser.execute("cancel 1")
        self.assertIn("[-] Alarm #1 cancelled", res)

    def test_unknown_command(self):
        res = self.parser.execute("foobar")
        self.assertIn("[-] Unknown command: 'foobar'", res)


if __name__ == "__main__":
    unittest.main()
