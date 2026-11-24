"""Habit-tracking logic. No web or file code lives here (see spec.md).

Every function that depends on the date takes ``today`` as an argument so
callers (and tests) control the clock.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

GOAL_DAYS = 60
MAX_NAME_LENGTH = 100


class AlreadyCheckedError(Exception):
    """Raised when a habit is checked off twice on the same day (R3)."""


@dataclass
class Habit:
    id: str
    name: str
    created: str  # ISO date
    checked_days: list[str] = field(default_factory=list)  # sorted ISO dates

    @property
    def days_checked(self) -> int:
        """Number of distinct days checked off; gaps don't reset it (R6, R7)."""
        return len(self.checked_days)

    @property
    def progress(self) -> int:
        """Progress toward the goal, capped at GOAL_DAYS for display (R6)."""
        return min(self.days_checked, GOAL_DAYS)

    @property
    def goal_reached(self) -> bool:
        return self.days_checked >= GOAL_DAYS

    def is_checked_on(self, day: date) -> bool:
        """True if checked on ``day``. Using the date gives the midnight reset (R4)."""
        return day.isoformat() in self.checked_days

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created": self.created,
            "checked_days": list(self.checked_days),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Habit:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            created=str(data["created"]),
            checked_days=sorted(set(data.get("checked_days", []))),
        )

    def view(self, today: date) -> dict:
        """Stored fields plus derived ones, for display."""
        return {
            **self.to_dict(),
            "checked_today": self.is_checked_on(today),
            "progress": self.progress,
            "goal": GOAL_DAYS,
            "goal_reached": self.goal_reached,
        }


@dataclass
class CheckResult:
    habit: Habit
    message: str
    goal_reached_now: bool


def _clean_name(name: object) -> str:
    if not isinstance(name, str):
        raise ValueError("Habit name must be text.")
    name = name.strip()
    if not name:
        raise ValueError("Habit name can't be empty.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Habit name must be at most {MAX_NAME_LENGTH} characters.")
    return name


class HabitTracker:
    """A user's collection of habits."""

    def __init__(self, habits: list[Habit] | None = None):
        self.habits: list[Habit] = list(habits or [])

    def get(self, habit_id: str) -> Habit:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit
        raise KeyError(habit_id)

    def add_habit(self, name: object, today: date) -> Habit:
        """R1: add a new habit with no check-offs."""
        name = _clean_name(name)
        if any(h.name.casefold() == name.casefold() for h in self.habits):
            raise ValueError(f'You already have a habit called "{name}".')
        habit = Habit(id=uuid.uuid4().hex, name=name, created=today.isoformat())
        self.habits.append(habit)
        return habit

    def remove_habit(self, habit_id: str) -> Habit:
        """R2: remove a habit and its history."""
        habit = self.get(habit_id)
        self.habits.remove(habit)
        return habit

    def check_off(self, habit_id: str, today: date) -> CheckResult:
        """R3/R5/R6/R8: record today's check-off and return a congratulation."""
        habit = self.get(habit_id)
        if habit.is_checked_on(today):
            raise AlreadyCheckedError(f"{habit.name} is already checked off today.")
        habit.checked_days = sorted(habit.checked_days + [today.isoformat()])

        if habit.days_checked == GOAL_DAYS:
            message = (
                f"You did it! {habit.name} has reached its {GOAL_DAYS}-day goal! "
                "That's a real habit now."
            )
            return CheckResult(habit, message, goal_reached_now=True)

        message = f"Nice work on {habit.name}! Day {habit.progress} of {GOAL_DAYS}."
        return CheckResult(habit, message, goal_reached_now=False)

    def view(self, today: date) -> list[dict]:
        return [h.view(today) for h in self.habits]

    def to_dict(self) -> dict:
        return {"habits": [h.to_dict() for h in self.habits]}

    @classmethod
    def from_dict(cls, data: dict) -> HabitTracker:
        return cls([Habit.from_dict(h) for h in data.get("habits", [])])
