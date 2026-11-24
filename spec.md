# Habit Tracker — Specification (v1)

This turns the requirements in `problem.md` into concrete, testable behavior.

## Shape of the program

- A small local web app. Running `python3 app.py` starts a server on
  `http://127.0.0.1:8000` and the user opens that page in a browser.
- Python standard library only (`http.server`, `json`, `datetime`, `unittest`).
  No third-party packages and no JavaScript build step; the page is a single
  HTML file with inline CSS and plain JavaScript.
- Logic lives in `habits.py` and does not depend on the web layer, so it can be
  unit-tested directly. `app.py` is a thin HTTP layer over it.

## Data model

A habit has:

| field          | meaning                                                         |
|----------------|-----------------------------------------------------------------|
| `id`           | unique string id, assigned on creation                         |
| `name`         | text the user typed (trimmed, 1–100 characters)                 |
| `created`      | ISO date (`YYYY-MM-DD`) the habit was added                     |
| `checked_days` | sorted list of distinct ISO dates on which it was checked off   |

Everything else (checked today, progress, goal reached) is **derived** from
`checked_days` and today's date, never stored separately.

`GOAL_DAYS = 60`.

## Requirements → behavior

- **R1 — Add a habit.** `add_habit(name)` creates a habit with an empty
  `checked_days`. The name is trimmed; an empty/whitespace-only name or a name
  over 100 characters is rejected with a `ValueError`. Duplicate names
  (case-insensitive) are rejected too, to avoid confusion.
- **R2 — Remove a habit.** `remove_habit(id)` deletes the habit and all its
  history. Removing an unknown id raises `KeyError`.
- **R3 — Once per day.** `check_off(id, today)` adds `today` to
  `checked_days`. If `today` is already there, it raises `AlreadyCheckedError`
  and nothing changes. (v1 does not support un-checking.)
- **R4 — Reset at midnight.** "Checked today" means "today's date, from the
  computer's local clock, is in `checked_days`". Because the date changes at
  local midnight, every checkmark appears cleared at midnight without any
  stored state being modified. The page also re-fetches state just after local
  midnight so an open tab updates on its own.
- **R5 — Congratulate every check-off.** A successful `check_off` returns a
  non-empty congratulation message that names the habit and shows progress
  (e.g. `"Nice work on Read! Day 12 of 60."`). The page displays it.
- **R6 — Per-habit 60-day goal.** Each habit's progress is
  `len(checked_days)`, shown as `n / 60`. Each habit is counted separately.
- **R7 — Missed days don't reset.** Progress counts distinct checked days, not
  a consecutive streak. A gap between check-offs leaves earlier days counted;
  the missed day simply adds nothing.
- **R8 — Congratulate on reaching the goal.** When a check-off makes progress
  reach exactly 60, the returned message is a special goal message
  (e.g. `"You did it! Read has reached its 60-day goal!"`) and the result is
  flagged `goal_reached_now = True`. A habit at or past 60 is shown as
  complete. Checking off after 60 still records the day and gives the normal
  R5 message; the displayed progress is capped at 60 / 60.
- **R9 — Persistence.** All habits and their `checked_days` are saved to
  `data/habits.json` after every change and loaded on start-up. Writes go to a
  temporary file that is then renamed, so a crash mid-write does not corrupt
  the file. A missing file means "no habits yet".

## HTTP API (used by the page)

| method & path                  | body           | result                              |
|--------------------------------|----------------|-------------------------------------|
| `GET /`                        |                | the HTML page                       |
| `GET /api/habits`              |                | `{today, goal, habits:[...]}`       |
| `POST /api/habits`             | `{"name": ..}` | new habit, or 400 with `error`      |
| `DELETE /api/habits/<id>`      |                | 204, or 404                         |
| `POST /api/habits/<id>/check`  |                | `{message, goal_reached_now, habit}`, 404, or 409 if already checked |

Each habit in a response includes the derived fields `checked_today`,
`progress` (capped at 60), and `goal_reached`.

## Out of scope for v1

Un-checking a day, editing a habit's name, multiple users, reminders or
notifications, history/calendar views, and hosting anywhere other than
localhost.
