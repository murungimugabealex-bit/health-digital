import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

from rules import SAFETY_NOTE, SYMPTOM_LABELS
from rules import assess as assess_signals

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "health_digital.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

SAMPLE_CASES = [
    {
        "id": "SYN-001",
        "label": "Sample 1: fever and cough",
        "inputs": {
            "age": 34, "temperature_c": 38.4, "heart_rate": 96,
            "respiratory_rate": 20, "systolic_bp": 118, "spo2": 97,
            "symptoms": ["fever", "cough"], "duration_days": 2,
        },
    },
    {
        "id": "SYN-002",
        "label": "Sample 2: low oxygen and chest pain",
        "inputs": {
            "age": 61, "temperature_c": 38.8, "heart_rate": 118,
            "respiratory_rate": 28, "systolic_bp": 104, "spo2": 90,
            "symptoms": ["fever", "cough", "shortness_of_breath", "chest_pain"],
            "duration_days": 1,
        },
    },
    {
        "id": "SYN-003",
        "label": "Sample 3: mild symptoms",
        "inputs": {
            "age": 25, "temperature_c": 36.8, "heart_rate": 74,
            "respiratory_rate": 16, "systolic_bp": 120, "spo2": 99,
            "symptoms": ["cough"], "duration_days": 1,
        },
    },
]


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def db_session():
    connection = get_db()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_session() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_code TEXT NOT NULL,
                created_at TEXT NOT NULL,
                age INTEGER NOT NULL,
                inputs_json TEXT NOT NULL,
                risk TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                recommendation TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_patients (
                code TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                inputs_json TEXT NOT NULL
            )
            """
        )
        for sample in SAMPLE_CASES:
            connection.execute(
                "INSERT OR IGNORE INTO synthetic_patients (code, label, inputs_json) VALUES (?, ?, ?)",
                (sample["id"], sample["label"], json.dumps(sample["inputs"])),
            )


init_db()


@app.context_processor
def inject_status():
    return {
        "guest_mode": bool(session.get("guest")),
        "signed_in_user": session.get("user"),
        "safety_note": SAFETY_NOTE,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/guest", methods=["POST"])
def guest():
    session["guest"] = True
    flash("Guest mode is on. All features are unlocked.")
    return redirect(url_for("assess"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == DEMO_USERNAME and password == DEMO_PASSWORD:
            session["user"] = username
            flash("Signed in with the demo account.")
            return redirect(url_for("assess"))
        flash("Those demo details are not correct. Try demo / demo123, or continue as guest.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have left the session.")
    return redirect(url_for("index"))


def parse_assessment_form(form):
    return {
        "age": int(form["age"]),
        "temperature_c": float(form["temperature_c"]),
        "heart_rate": int(form["heart_rate"]),
        "respiratory_rate": int(form["respiratory_rate"]),
        "systolic_bp": int(form["systolic_bp"]),
        "spo2": int(form["spo2"]),
        "symptoms": [s for s in form.getlist("symptoms") if s in SYMPTOM_LABELS],
        "duration_days": int(form["duration_days"]),
    }


@app.route("/assess", methods=["GET", "POST"])
def assess():
    if request.method == "POST":
        try:
            inputs = parse_assessment_form(request.form)
        except (KeyError, TypeError, ValueError):
            flash("Please check every field. Numbers are required.")
            return render_template("assess.html", values=request.form.to_dict(), samples=SAMPLE_CASES)
        if not 0 <= inputs["age"] <= 120 or not 0 <= inputs["spo2"] <= 100:
            flash("Age must be 0-120 and SpO2 must be 0-100.")
            return render_template("assess.html", values=request.form.to_dict(), samples=SAMPLE_CASES)

        result = assess_signals(**inputs)
        patient_code = (request.form.get("patient_code", "").strip() or "GUEST")[:40]
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with db_session() as connection:
            cursor = connection.execute(
                """
                INSERT INTO assessments
                (patient_code, created_at, age, inputs_json, risk, reasons_json, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_code,
                    created_at,
                    inputs["age"],
                    json.dumps(inputs),
                    result["risk"],
                    json.dumps(result["reasons"]),
                    result["recommendation"],
                ),
            )
            record_id = cursor.lastrowid
        return redirect(url_for("result", record_id=record_id))

    return render_template("assess.html", values={}, samples=SAMPLE_CASES)


def row_to_record(row):
    record = dict(row)
    record["inputs"] = json.loads(record["inputs_json"])
    record["reasons"] = json.loads(record["reasons_json"])
    return record


@app.route("/result/<int:record_id>")
def result(record_id):
    with db_session() as connection:
        row = connection.execute(
            "SELECT * FROM assessments WHERE id = ?", (record_id,)
        ).fetchone()
    if row is None:
        abort(404)
    return render_template("result.html", record=row_to_record(row))


@app.route("/history")
def history():
    with db_session() as connection:
        rows = connection.execute(
            "SELECT * FROM assessments ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return render_template("history.html", records=[row_to_record(row) for row in rows])


@app.errorhandler(404)
def not_found(_error):
    return render_template("not_found.html"), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
