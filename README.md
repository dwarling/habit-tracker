# Habit Tracker

A small habit tracker that runs in your browser on your own computer. It helps
you stick with new habits for the roughly two months it takes for them to form.

- Add and remove habits.
- Check off each habit once a day. You get a congratulation every time.
- Checkmarks reset at midnight on your computer's clock.
- Each habit has its own 60-day goal. Each day you check it off counts toward
  the goal. Missing a day doesn't reset your progress; that day just doesn't
  count.
- You get a special congratulation when a habit reaches 60 days.
- Everything is saved to `data/habits.json`, so it is still there after you
  close the browser or restart the app.

It uses only the Python standard library (Python 3.10+). Nothing to install.

## Run it

```sh
python3 app.py
```

Then open <http://127.0.0.1:8000>. Stop it with Ctrl+C.

Options: `--port 8080` to use a different port, `--data path/to/file.json` to
save somewhere else.

## Run the tests

```sh
python3 -m unittest discover -s tests -v
```

Each test name includes the requirement IDs (R1–R9 from `problem.md`) it checks.

## Files

| file                 | what it is                                     |
|----------------------|------------------------------------------------|
| `problem.md`         | the problem and requirements R1–R9             |
| `spec.md`            | how each requirement is implemented            |
| `habits.py`          | habit logic (no web or file code)              |
| `storage.py`         | saving/loading `data/habits.json`              |
| `app.py`             | local web server and JSON API                  |
| `static/index.html`  | the page                                       |
| `tests/`             | `unittest` tests                               |
