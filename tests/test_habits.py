"""Tests for habit logic in habits.py. Each test names the requirement(s) it checks."""

import unittest
from datetime import date, timedelta

from habits import GOAL_DAYS, AlreadyCheckedError, HabitTracker

DAY1 = date(2026, 1, 1)


def check_n_days(tracker, habit_id, n, start=DAY1, step=1):
    """Check a habit off on n days, ``step`` days apart. Returns the last result."""
    result = None
    for i in range(n):
        result = tracker.check_off(habit_id, start + timedelta(days=i * step))
    return result


class AddHabitTests(unittest.TestCase):
    def test_r1_add_habit(self):
        tracker = HabitTracker()
        habit = tracker.add_habit("Read", DAY1)
        self.assertEqual([h.name for h in tracker.habits], ["Read"])
        self.assertEqual(habit.checked_days, [])
        self.assertEqual(habit.created, "2026-01-01")

    def test_r1_name_is_trimmed(self):
        habit = HabitTracker().add_habit("  Stretch  ", DAY1)
        self.assertEqual(habit.name, "Stretch")

    def test_r1_rejects_empty_name(self):
        tracker = HabitTracker()
        for bad in ["", "   ", None, 5]:
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    tracker.add_habit(bad, DAY1)
        self.assertEqual(tracker.habits, [])

    def test_r1_rejects_too_long_name(self):
        with self.assertRaises(ValueError):
            HabitTracker().add_habit("x" * 101, DAY1)

    def test_r1_rejects_duplicate_name_case_insensitive(self):
        tracker = HabitTracker()
        tracker.add_habit("Read", DAY1)
        with self.assertRaises(ValueError):
            tracker.add_habit("read", DAY1)
        self.assertEqual(len(tracker.habits), 1)

    def test_r1_ids_are_unique(self):
        tracker = HabitTracker()
        a = tracker.add_habit("A", DAY1)
        b = tracker.add_habit("B", DAY1)
        self.assertNotEqual(a.id, b.id)


class RemoveHabitTests(unittest.TestCase):
    def test_r2_remove_habit(self):
        tracker = HabitTracker()
        keep = tracker.add_habit("Keep", DAY1)
        drop = tracker.add_habit("Drop", DAY1)
        tracker.remove_habit(drop.id)
        self.assertEqual([h.id for h in tracker.habits], [keep.id])

    def test_r2_remove_unknown_raises(self):
        with self.assertRaises(KeyError):
            HabitTracker().remove_habit("nope")

    def test_r2_removed_name_can_be_reused(self):
        tracker = HabitTracker()
        old = tracker.add_habit("Read", DAY1)
        tracker.check_off(old.id, DAY1)
        tracker.remove_habit(old.id)
        new = tracker.add_habit("Read", DAY1)
        self.assertEqual(new.days_checked, 0)


class CheckOffTests(unittest.TestCase):
    def setUp(self):
        self.tracker = HabitTracker()
        self.habit = self.tracker.add_habit("Read", DAY1)

    def test_r3_check_off_marks_today(self):
        self.tracker.check_off(self.habit.id, DAY1)
        self.assertTrue(self.habit.is_checked_on(DAY1))

    def test_r3_cannot_check_twice_same_day(self):
        self.tracker.check_off(self.habit.id, DAY1)
        with self.assertRaises(AlreadyCheckedError):
            self.tracker.check_off(self.habit.id, DAY1)
        self.assertEqual(self.habit.days_checked, 1)

    def test_r3_check_off_unknown_raises(self):
        with self.assertRaises(KeyError):
            self.tracker.check_off("nope", DAY1)

    def test_r3_habits_are_checked_independently(self):
        other = self.tracker.add_habit("Walk", DAY1)
        self.tracker.check_off(self.habit.id, DAY1)
        self.assertFalse(other.is_checked_on(DAY1))

    def test_r4_checkmark_clears_on_next_day(self):
        self.tracker.check_off(self.habit.id, DAY1)
        next_day = DAY1 + timedelta(days=1)
        self.assertFalse(self.habit.is_checked_on(next_day))
        self.assertFalse(self.tracker.view(next_day)[0]["checked_today"])
        self.assertTrue(self.tracker.view(DAY1)[0]["checked_today"])

    def test_r4_can_check_again_after_midnight(self):
        self.tracker.check_off(self.habit.id, DAY1)
        self.tracker.check_off(self.habit.id, DAY1 + timedelta(days=1))
        self.assertEqual(self.habit.days_checked, 2)

    def test_r4_reset_keeps_progress(self):
        self.tracker.check_off(self.habit.id, DAY1)
        view = self.tracker.view(DAY1 + timedelta(days=1))[0]
        self.assertFalse(view["checked_today"])
        self.assertEqual(view["progress"], 1)

    def test_r5_every_check_off_congratulates(self):
        for i in range(3):
            result = self.tracker.check_off(self.habit.id, DAY1 + timedelta(days=i))
            with self.subTest(day=i + 1):
                self.assertIn("Read", result.message)
                self.assertIn(f"Day {i + 1} of {GOAL_DAYS}", result.message)
                self.assertFalse(result.goal_reached_now)


class GoalTests(unittest.TestCase):
    def setUp(self):
        self.tracker = HabitTracker()
        self.habit = self.tracker.add_habit("Read", DAY1)

    def test_r6_goal_is_60_days(self):
        self.assertEqual(GOAL_DAYS, 60)
        self.assertEqual(self.tracker.view(DAY1)[0]["goal"], 60)

    def test_r6_each_check_off_counts_toward_goal(self):
        check_n_days(self.tracker, self.habit.id, 5)
        self.assertEqual(self.habit.progress, 5)

    def test_r6_each_habit_has_its_own_progress(self):
        other = self.tracker.add_habit("Walk", DAY1)
        check_n_days(self.tracker, self.habit.id, 3)
        check_n_days(self.tracker, other.id, 1)
        self.assertEqual(self.habit.progress, 3)
        self.assertEqual(other.progress, 1)

    def test_r7_missed_day_does_not_reset_progress(self):
        self.tracker.check_off(self.habit.id, DAY1)
        self.tracker.check_off(self.habit.id, DAY1 + timedelta(days=1))
        # Day 3 missed.
        self.tracker.check_off(self.habit.id, DAY1 + timedelta(days=3))
        self.assertEqual(self.habit.progress, 3)

    def test_r7_missed_days_do_not_count(self):
        # Checked every other day across 20 calendar days -> 10 counted.
        check_n_days(self.tracker, self.habit.id, 10, step=2)
        self.assertEqual(self.habit.progress, 10)

    def test_r8_congratulates_when_goal_reached(self):
        check_n_days(self.tracker, self.habit.id, GOAL_DAYS - 1)
        self.assertFalse(self.habit.goal_reached)
        result = self.tracker.check_off(self.habit.id, DAY1 + timedelta(days=GOAL_DAYS - 1))
        self.assertTrue(result.goal_reached_now)
        self.assertTrue(self.habit.goal_reached)
        self.assertIn("60-day goal", result.message)
        self.assertIn("Read", result.message)

    def test_r7_r8_goal_reached_despite_gaps(self):
        result = check_n_days(self.tracker, self.habit.id, GOAL_DAYS, step=3)
        self.assertTrue(result.goal_reached_now)

    def test_r8_goal_message_only_once(self):
        check_n_days(self.tracker, self.habit.id, GOAL_DAYS)
        result = self.tracker.check_off(self.habit.id, DAY1 + timedelta(days=GOAL_DAYS))
        self.assertFalse(result.goal_reached_now)
        self.assertTrue(result.message)  # R5 still applies
        self.assertTrue(self.habit.goal_reached)

    def test_r6_r8_progress_capped_at_goal(self):
        check_n_days(self.tracker, self.habit.id, GOAL_DAYS + 5)
        self.assertEqual(self.habit.progress, GOAL_DAYS)
        self.assertEqual(self.habit.days_checked, GOAL_DAYS + 5)


class SerializationTests(unittest.TestCase):
    def test_r9_round_trip_through_dict(self):
        tracker = HabitTracker()
        habit = tracker.add_habit("Read", DAY1)
        tracker.check_off(habit.id, DAY1)
        tracker.check_off(habit.id, DAY1 + timedelta(days=2))

        restored = HabitTracker.from_dict(tracker.to_dict())
        self.assertEqual(restored.to_dict(), tracker.to_dict())
        self.assertEqual(restored.get(habit.id).progress, 2)
        self.assertTrue(restored.get(habit.id).is_checked_on(DAY1))

    def test_r3_r9_from_dict_dedupes_and_sorts_days(self):
        data = {"habits": [{"id": "x", "name": "Read", "created": "2026-01-01",
                            "checked_days": ["2026-01-03", "2026-01-01", "2026-01-03"]}]}
        habit = HabitTracker.from_dict(data).get("x")
        self.assertEqual(habit.checked_days, ["2026-01-01", "2026-01-03"])


if __name__ == "__main__":
    unittest.main()
