"""
Unit tests for Notifier implementations.
"""

import io
import unittest
from datetime import datetime, timezone
from alarm_clock.domain import Alarm
from alarm_clock.notifier import TerminalNotifier, TestNotifier


class TestNotifierImplementations(unittest.TestCase):
    def setUp(self):
        self.tz = timezone.utc
        self.now = datetime(2026, 9, 3, 12, 0, 0, tzinfo=self.tz)
        self.alarm = Alarm(id=1, target_time=self.now, label="Wake up")

    def test_terminal_notifier_output(self):
        output_stream = io.StringIO()
        notifier = TerminalNotifier(stream=output_stream, ring_bell=True)
        notifier.notify(self.alarm)

        output = output_stream.getvalue()
        self.assertIn("ALARM TRIGGERED! #1", output)
        self.assertIn("Wake up", output)
        self.assertIn("\a", output)

    def test_test_notifier_captures_alarm(self):
        notifier = TestNotifier()
        self.assertEqual(len(notifier.notifications), 0)

        notifier.notify(self.alarm)
        self.assertEqual(len(notifier.notifications), 1)
        self.assertEqual(notifier.notifications[0].id, 1)

        notifier.reset()
        self.assertEqual(len(notifier.notifications), 0)


if __name__ == "__main__":
    unittest.main()
