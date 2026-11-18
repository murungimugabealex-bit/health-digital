import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from rules import assess  # noqa: E402


class RuleTests(unittest.TestCase):
    def base_inputs(self):
        return {
            "age": 30,
            "temperature_c": 36.8,
            "heart_rate": 75,
            "respiratory_rate": 16,
            "systolic_bp": 120,
            "spo2": 98,
            "symptoms": ["cough"],
            "duration_days": 1,
        }

    def test_low_risk(self):
        result = assess(**self.base_inputs())
        self.assertEqual(result["risk"], "Low")
        self.assertTrue(result["reasons"])

    def test_medium_risk(self):
        inputs = self.base_inputs()
        inputs["symptoms"] = ["fever", "cough"]
        inputs["temperature_c"] = 38.5
        result = assess(**inputs)
        self.assertEqual(result["risk"], "Medium")

    def test_high_risk_for_low_oxygen(self):
        inputs = self.base_inputs()
        inputs["spo2"] = 90
        result = assess(**inputs)
        self.assertEqual(result["risk"], "High")
        self.assertTrue(any("Oxygen" in reason for reason in result["reasons"]))

    def test_high_risk_for_chest_pain(self):
        inputs = self.base_inputs()
        inputs["symptoms"] = ["chest_pain"]
        result = assess(**inputs)
        self.assertEqual(result["risk"], "High")

    def test_safety_note_present(self):
        result = assess(**self.base_inputs())
        self.assertIn("doctor or nurse makes the final decision", result["safety_note"])


class AppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_has_guest_button(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Continue as Guest", response.data)

    def test_guest_unlocks_all_features(self):
        self.client.post("/guest", follow_redirects=True)
        for path in ("/assess", "/history", "/login"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
        self.assertIn(b"Guest mode: all features on", self.client.get("/assess").data)

    def test_demo_login(self):
        response = self.client.post(
            "/login",
            data={"username": "demo", "password": "demo123"},
            follow_redirects=True,
        )
        self.assertIn(b"Demo user: demo", response.data)

    def test_bad_demo_login_shows_help(self):
        response = self.client.post(
            "/login",
            data={"username": "wrong", "password": "wrong"},
            follow_redirects=True,
        )
        self.assertIn(b"demo / demo123", response.data)

    def test_assessment_flow_saves_and_shows_result(self):
        self.client.post("/guest")
        response = self.client.post(
            "/assess",
            data={
                "patient_code": "SYN-TEST",
                "age": "61",
                "temperature_c": "38.8",
                "heart_rate": "118",
                "respiratory_rate": "28",
                "systolic_bp": "104",
                "spo2": "90",
                "duration_days": "1",
                "symptoms": ["fever", "shortness_of_breath", "chest_pain"],
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"HIGH RISK", response.data)
        self.assertIn(b"doctor or nurse makes the final decision", response.data)
        self.assertIn(b"SYN-TEST", self.client.get("/history").data)


if __name__ == "__main__":
    unittest.main()
