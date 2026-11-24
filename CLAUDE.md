# CLAUDE.md

Guidance for working in this repository.

## Project

A local habit tracker web app. `problem.md` has the requirements (R1–R9);
`spec.md` has the concrete behavior. When the two disagree, follow `spec.md`
and point out the mismatch.

## Rules

- Python standard library only. Do not add third-party packages, a
  `requirements.txt`, or a JavaScript build step.
- Keep logic in `habits.py`, separate from the HTTP layer (`app.py`) and the
  page (`static/index.html`). `habits.py` must not import from `app.py`.
- Functions that depend on the date take `today` as a parameter, so tests
  can control time. Only the HTTP layer reads the real clock
  (`datetime.date.today()`, local time).
- Store only facts (`checked_days`). Work out progress, checked-today and
  goal-reached when needed instead of saving them.
- Saved data goes in `data/`, which is git-ignored. Never commit user data.

## Tests

- `unittest` only. Tests live in `tests/` and cover logic and persistence,
  not page layout.
- Every test names the requirement IDs it checks, in its name or docstring
  (e.g. `test_r3_cannot_check_twice_same_day`).
- Run all tests with: `python3 -m unittest discover -s tests -v`
- Run the tests before every commit.

## Git

- Small commits whose messages say what changed and why.
- Show the commit message to the user before committing.
- Never amend, rebase, reset, or otherwise rewrite or undo a commit. Fix
  mistakes with a new commit.
