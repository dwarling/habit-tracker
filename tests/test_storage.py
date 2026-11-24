"""Tests for persistence in storage.py (R9)."""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import storage
from habits import GOAL_DAYS, HabitTracker

DAY1 = date(2026, 1, 1)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = Path(self._dir.name) / "data" / "habits.json"

    def tearDown(self):
        self._dir.cleanup()

    def test_r9_missing_file_loads_empty(self):
        self.assertEqual(storage.load(self.path).habits, [])

    def test_r9_habits_checkmarks_and_progress_survive_restart(self):
        tracker = HabitTracker()
        read = tracker.add_habit("Read", DAY1)
        walk = tracker.add_habit("Walk", DAY1)
        tracker.check_off(read.id, DAY1)
        tracker.check_off(read.id, DAY1 + timedelta(days=2))
        tracker.check_off(walk.id, DAY1 + timedelta(days=2))
        storage.save(tracker, self.path)

        reloaded = storage.load(self.path)
        self.assertEqual([h.name for h in reloaded.habits], ["Read", "Walk"])
        self.assertEqual(reloaded.get(read.id).progress, 2)
        self.assertTrue(reloaded.get(walk.id).is_checked_on(DAY1 + timedelta(days=2)))

    def test_r2_r9_removal_is_saved(self):
        tracker = HabitTracker()
        habit = tracker.add_habit("Read", DAY1)
        storage.save(tracker, self.path)
        tracker.remove_habit(habit.id)
        storage.save(tracker, self.path)
        self.assertEqual(storage.load(self.path).habits, [])

    def test_r3_r9_once_per_day_still_enforced_after_reload(self):
        from habits import AlreadyCheckedError

        tracker = HabitTracker()
        habit = tracker.add_habit("Read", DAY1)
        tracker.check_off(habit.id, DAY1)
        storage.save(tracker, self.path)

        reloaded = storage.load(self.path)
        with self.assertRaises(AlreadyCheckedError):
            reloaded.check_off(habit.id, DAY1)

    def test_r8_r9_goal_reached_survives_reload(self):
        tracker = HabitTracker()
        habit = tracker.add_habit("Read", DAY1)
        for i in range(GOAL_DAYS):
            tracker.check_off(habit.id, DAY1 + timedelta(days=i))
        storage.save(tracker, self.path)
        self.assertTrue(storage.load(self.path).get(habit.id).goal_reached)

    def test_r9_corrupt_file_raises_instead_of_wiping(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(ValueError):
            storage.load(self.path)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not json")

    def test_r9_save_leaves_no_temp_files(self):
        storage.save(HabitTracker(), self.path)
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ["habits.json"])


if __name__ == "__main__":
    unittest.main()
