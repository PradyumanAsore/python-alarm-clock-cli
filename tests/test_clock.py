"""
Unit tests for Clock abstraction implementations.
"""

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from alarm_clock.clock import SystemClock, TestClock


class TestClockImplementations(unittest.TestCase):
    def test_system_clock_now_is_timezone_aware(self):
        clock = SystemClock()
        now = clock.now()
        self.assertIsNotNone(now.tzinfo)
        self.assertIsInstance(now, datetime)

    def test_test_clock_initialization(self):
        tz = timezone.utc
        start_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=tz)
        clock = TestClock(start_time)
        self.assertEqual(clock.now(), start_time)

    def test_test_clock_naive_raises_error(self):
        start_time = datetime(2026, 9, 3, 12, 0, 0)
        with self.assertRaises(ValueError):
            TestClock(start_time)

    def test_test_clock_advance_seconds(self):
        tz = timezone.utc
        start_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=tz)
        clock = TestClock(start_time)

        clock.advance(30.0)
        self.assertEqual(clock.now(), start_time + timedelta(seconds=30))

    def test_test_clock_advance_timedelta(self):
        tz = timezone.utc
        start_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=tz)
        clock = TestClock(start_time)

        clock.advance(timedelta(minutes=15))
        self.assertEqual(clock.now(), start_time + timedelta(minutes=15))

    def test_test_clock_advance_negative_raises_error(self):
        tz = timezone.utc
        clock = TestClock(datetime(2026, 9, 3, 12, 0, 0, tzinfo=tz))
        with self.assertRaises(ValueError):
            clock.advance(-10)

    def test_test_clock_async_sleep(self):
        async def run_async_test():
            tz = timezone.utc
            start_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=tz)
            clock = TestClock(start_time)

            await clock.sleep(60.0)
            self.assertEqual(clock.now(), start_time + timedelta(seconds=60))

        asyncio.run(run_async_test())


if __name__ == "__main__":
    unittest.main()
