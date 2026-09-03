# Alarm Clock CLI — Senior Engineering Assessment

A production-grade, zero-dependency Python CLI Alarm Clock application built using Python 3.10+ standard library primitives.

---

## Architecture Overview

```
+-------------------------------------------------------+
|                    CLI / REPL Layer                   |
|                   (src/alarm_clock/cli.py)            |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                 Alarm Service Layer                   |
|                 (src/alarm_clock/service.py)          |
+---------------------------+---------------------------+
                            |
           +----------------+----------------+
           |                                 |
           v                                 v
+-----------------------+       +-----------------------+
|      Domain Layer     |       |    Clock & Notifier   |
| (src/alarm_clock/     |       | (src/alarm_clock/     |
|   domain.py)          |       |  clock.py, notifier.py|
+-----------------------+       +-----------------------+
```

---

## Important Engineering Decisions

| Decision | Chosen Approach | Rationale | Alternatives Considered |
| :--- | :--- | :--- | :--- |
| **Concurrency & Architecture** | Single-process `asyncio` REPL event loop. | Eliminates inter-process IPC, PID locks, and socket servers while allowing non-blocking command entry and background alarm monitoring. | Subcommand daemon (heavy IPC), Multi-threading (risk of race conditions). |
| **Dependencies** | Pure Python standard library (`>=3.10`). | Zero external `pip` dependencies. Maximum portability, zero security supply chain risks. | Third-party TUI/Audio packages (`textual`, `pygame`). |
| **Time Representation** | Timezone-aware local `datetime` (`astimezone()`). | Human alarms are local-time based (`07:30 AM local`). Prevents naive vs aware comparison bugs and DST errors. | UTC-only (confusing UX for local users), Naive datetime (bug-prone). |
| **Testability of Time** | `Clock` protocol (`SystemClock` & `TestClock`). | 100% deterministic test suite. Tests advance time instantaneously without real `time.sleep()`. | `unittest.mock.patch` on `datetime.now` (fragile, leaky), Real sleeping (extremely slow tests). |
| **Clock Loop Efficiency** | Dynamic sleep capped at `1.0s` (`min(secs_left, 1.0)`). | Dynamic sleep ensures `0% CPU` usage when idle. The `1.0s` upper cap guarantees instant reaction to new short alarms or clock drift. | Busy loop (100% CPU pinning), Static `sleep(60)` (sluggish reaction). |
| **Past Time Resolution** | Auto-advance `HH:MM` to tomorrow if time has already passed today. | Intuitive human UX ("setting 07:00 at 08:30 means 07:00 tomorrow"). | Reject with error (frustrating UX requiring full ISO dates). |

---

## Getting Started

### Prerequisites
* Python 3.10 or higher.

### Running the Application

Execute directly from the workspace root:

```bash
python -m alarm_clock
```

---

## Usage & Commands

```text
============================================================
  ⏰ ALARM CLOCK CLI
  Type 'help' for available commands or 'exit' to quit.
============================================================
alarm> add 07:30 Wake up for morning meeting
[+] Alarm #1 created for 2026-09-04 07:30:00

alarm> add +10m Check baking oven
[+] Alarm #2 created for 2026-09-03 18:25:00

alarm> add 08:00 Workday alarm --weekdays
[+] Alarm #3 created for 2026-09-04 08:00:00 (weekdays)

alarm> list
ID   Status      Target Time          Effective Time       Recurring  Label
--------------------------------------------------------------------------------
1    PENDING     2026-09-04 07:30:00  2026-09-04 07:30:00  None       Wake up for morning meeting
2    PENDING     2026-09-03 18:25:00  2026-09-03 18:25:00  None       Check baking oven
3    PENDING     2026-09-04 08:00:00  2026-09-04 08:00:00  Weekdays   Workday alarm

alarm> snooze 2 10
[zZz] Alarm #2 snoozed until 18:35:00 (10m).

alarm> dismiss 2
[x] Alarm #2 dismissed.

alarm> cancel 1
[-] Alarm #1 cancelled.

alarm> exit
Goodbye!
```

---

## Running Unit Tests

Run the complete test suite (48 tests covering domain logic, clock providers, service triggers, CLI parsing, and edge cases):

```bash
# On Windows PowerShell
$env:PYTHONPATH="src"; python -m unittest discover -s tests

# On Linux / macOS
PYTHONPATH=src python3 -m unittest discover -s tests
```

---

## Interviewer Q&A Guide

### Q1: Why did you choose an interactive REPL instead of a background daemon?
**Answer**: An interactive REPL using `asyncio` allows background alarm monitoring and user commands to run concurrently inside a single process without needing IPC (sockets, RPC), PID files, or OS-specific background services. It keeps the architecture lightweight, simple, and self-contained.

### Q2: How do you prevent time-dependent unit tests from being slow or flaky?
**Answer**: We injected a `Clock` protocol into `AlarmService`. In production, `SystemClock` uses real time. In tests, `TestClock` allows setting simulated starting times and advancing clock state instantaneously via `clock.advance()`. This allows testing hours or days of alarm scheduling in milliseconds.

### Q3: What happens if the computer goes to sleep and wakes up past the alarm time?
**Answer**: Our dynamic ticker calculates `sleep_time = min(secs_left, 1.0)`. Upon waking up from sleep, the loop immediately executes `tick()`. Any past-due pending alarms are identified (`current_time >= effective_time`) and triggered instantly with a notification banner.

### Q4: How does the system handle multiple alarms set for the exact same second?
**Answer**: `AlarmService.tick()` iterates over all registered alarms during a single tick. Any alarm whose `effective_time <= now` is triggered in order. No alarm is skipped or dropped.
