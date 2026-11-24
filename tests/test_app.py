"""Tests for the HTTP API in app.py (routing and status codes, not page layout)."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import storage
from app import HabitApp, make_server
from habits import GOAL_DAYS


class ApiTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self._dir.name) / "habits.json"
        self.today = date(2026, 1, 1)
        self.app = HabitApp(self.data_path, clock=lambda: self.today)
        self.server = make_server(self.app, port=0)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, args=(0.01,), daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self._dir.cleanup()

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as res:
                raw = res.read()
                return res.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raw = e.read()
            return e.code, json.loads(raw) if raw else None

    def add(self, name="Read"):
        status, habit = self.request("POST", "/api/habits", {"name": name})
        self.assertEqual(status, 201)
        return habit

    def test_r1_add_via_api(self):
        habit = self.add("Read")
        self.assertEqual(habit["name"], "Read")
        _, state = self.request("GET", "/api/habits")
        self.assertEqual([h["name"] for h in state["habits"]], ["Read"])

    def test_r1_add_bad_name_is_400(self):
        status, body = self.request("POST", "/api/habits", {"name": "   "})
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_r2_remove_via_api(self):
        habit = self.add()
        status, _ = self.request("DELETE", f"/api/habits/{habit['id']}")
        self.assertEqual(status, 204)
        _, state = self.request("GET", "/api/habits")
        self.assertEqual(state["habits"], [])
        self.assertEqual(self.request("DELETE", f"/api/habits/{habit['id']}")[0], 404)

    def test_r3_r5_check_off_via_api(self):
        habit = self.add()
        status, body = self.request("POST", f"/api/habits/{habit['id']}/check")
        self.assertEqual(status, 200)
        self.assertIn("Read", body["message"])
        self.assertTrue(body["habit"]["checked_today"])
        status, _ = self.request("POST", f"/api/habits/{habit['id']}/check")
        self.assertEqual(status, 409)

    def test_r3_check_unknown_is_404(self):
        self.assertEqual(self.request("POST", "/api/habits/nope/check")[0], 404)

    def test_r4_api_uses_clock_for_reset(self):
        habit = self.add()
        self.request("POST", f"/api/habits/{habit['id']}/check")
        self.today += timedelta(days=1)
        _, state = self.request("GET", "/api/habits")
        self.assertEqual(state["today"], "2026-01-02")
        self.assertFalse(state["habits"][0]["checked_today"])
        self.assertEqual(state["habits"][0]["progress"], 1)

    def test_r6_r8_goal_via_api(self):
        habit = self.add()
        for _ in range(GOAL_DAYS - 1):
            self.request("POST", f"/api/habits/{habit['id']}/check")
            self.today += timedelta(days=1)
        _, body = self.request("POST", f"/api/habits/{habit['id']}/check")
        self.assertTrue(body["goal_reached_now"])
        self.assertTrue(body["habit"]["goal_reached"])
        self.assertEqual(body["habit"]["progress"], GOAL_DAYS)

    def test_r9_changes_are_saved_to_disk(self):
        habit = self.add()
        self.request("POST", f"/api/habits/{habit['id']}/check")
        reloaded = storage.load(self.data_path)
        self.assertTrue(reloaded.get(habit["id"]).is_checked_on(self.today))

    def test_page_is_served(self):
        with urllib.request.urlopen(self.base + "/") as res:
            self.assertEqual(res.status, 200)
            self.assertIn("text/html", res.headers["Content-Type"])

    def test_unknown_path_is_404(self):
        self.assertEqual(self.request("GET", "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
