"""Local web server for the habit tracker. Run: python3 app.py

A thin HTTP layer over habits.py and storage.py (see spec.md, "HTTP API").
This is the only module that reads the real clock.
"""

from __future__ import annotations

import argparse
import json
import threading
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

import storage
from habits import GOAL_DAYS, AlreadyCheckedError, HabitTracker

PAGE = Path(__file__).resolve().parent / "static" / "index.html"
MAX_BODY = 10_000


class HabitApp:
    """Holds the tracker, its save path, and the clock, behind a lock."""

    def __init__(self, data_path: Path, clock: Callable[[], date] = date.today):
        self.data_path = Path(data_path)
        self.clock = clock
        self.lock = threading.Lock()
        self.tracker: HabitTracker = storage.load(self.data_path)

    def save(self) -> None:
        storage.save(self.tracker, self.data_path)


def make_handler(app: HabitApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "HabitTracker/1"

        # --- helpers -------------------------------------------------------
        def _send(self, status: int, body: bytes = b"", ctype: str = "application/json"):
            self.send_response(status)
            if body:
                self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if body and self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, data: dict):
            self._send(status, json.dumps(data).encode("utf-8"))

        def _error(self, status: int, message: str):
            self._json(status, {"error": message})

        def _read_json(self) -> dict | None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return None
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None
            return data if isinstance(data, dict) else None

        def _parts(self) -> list[str]:
            return [p for p in self.path.split("?", 1)[0].split("/") if p]

        def log_message(self, format, *args):  # keep the terminal quiet
            pass

        # --- routes --------------------------------------------------------
        def do_GET(self):
            parts = self._parts()
            if parts == []:
                self._send(HTTPStatus.OK, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif parts == ["api", "habits"]:
                with app.lock:
                    today = app.clock()
                    self._json(HTTPStatus.OK, {
                        "today": today.isoformat(),
                        "goal": GOAL_DAYS,
                        "habits": app.tracker.view(today),
                    })
            else:
                self._error(HTTPStatus.NOT_FOUND, "Not found.")

        def do_POST(self):
            parts = self._parts()
            if parts == ["api", "habits"]:
                body = self._read_json()
                if body is None:
                    return self._error(HTTPStatus.BAD_REQUEST, "Expected a JSON object.")
                with app.lock:
                    today = app.clock()
                    try:
                        habit = app.tracker.add_habit(body.get("name"), today)
                    except ValueError as e:
                        return self._error(HTTPStatus.BAD_REQUEST, str(e))
                    app.save()
                    self._json(HTTPStatus.CREATED, habit.view(today))
            elif len(parts) == 4 and parts[:2] == ["api", "habits"] and parts[3] == "check":
                with app.lock:
                    today = app.clock()
                    try:
                        result = app.tracker.check_off(parts[2], today)
                    except KeyError:
                        return self._error(HTTPStatus.NOT_FOUND, "No such habit.")
                    except AlreadyCheckedError as e:
                        return self._error(HTTPStatus.CONFLICT, str(e))
                    app.save()
                    self._json(HTTPStatus.OK, {
                        "message": result.message,
                        "goal_reached_now": result.goal_reached_now,
                        "habit": result.habit.view(today),
                    })
            else:
                self._error(HTTPStatus.NOT_FOUND, "Not found.")

        def do_DELETE(self):
            parts = self._parts()
            if len(parts) == 3 and parts[:2] == ["api", "habits"]:
                with app.lock:
                    try:
                        app.tracker.remove_habit(parts[2])
                    except KeyError:
                        return self._error(HTTPStatus.NOT_FOUND, "No such habit.")
                    app.save()
                self._send(HTTPStatus.NO_CONTENT)
            else:
                self._error(HTTPStatus.NOT_FOUND, "Not found.")

    return Handler


def make_server(app: HabitApp, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(app))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the habit tracker.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data", type=Path, default=storage.DEFAULT_PATH,
                        help="where habits are saved (default: data/habits.json)")
    args = parser.parse_args()

    server = make_server(HabitApp(args.data), port=args.port)
    print(f"Habit tracker running at http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
