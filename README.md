# Signal to Support - demo system

A simple working prototype for the Future Health Digital Innovation Challenge
("From signals to solutions"). A community health worker enters symptoms and
vital signs and gets a Low / Medium / High risk hint, a short plain-English
reason, and a recommended next step.

**This is a challenge demo, not a medical device. It uses synthetic data only.
A doctor or nurse makes the final decision.**

## The idea in one line

A web app where a community health worker enters symptoms and vitals, and it
flags who needs urgent referral - with the reason shown on screen.

## Five core features

1. Continue as Guest button - opens every feature with no login.
2. Assessment form - patient code, age, days ill, six vital signs, six symptoms.
3. Load a synthetic sample case - fills the whole form with one click.
4. Transparent rule-based result - risk level, reasons, and next step.
5. Save and review - SQLite storage with a history table and detail view.

## Project structure

```
health digital/
  app.py                     Flask routes, SQLite storage, session/guest access
  rules.py                   Risk rules (no machine learning, no hidden model)
  requirements.txt           Python dependencies
  templates/
    base.html                Shared layout, navigation, safety note
    index.html               Home page with Continue as Guest
    assess.html              Assessment form and sample-case loader
    result.html              Risk result, reasons, recommendation
    history.html             Last 20 saved assessments
    login.html               Optional demo login
    not_found.html           404 page
  static/
    style.css                All styling, no external assets
  tests/
    test_app.py              10 automated checks (unittest)
  data/
    health_digital.db        Created automatically on first run (SQLite)
  README.md                  This file
  REPORT.md                  Slide-ready submission text
```

## Run instructions

Requires Python 3.10 or newer. From this folder:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in a browser.

- Click **Continue as Guest** to unlock all features.
- Optional demo login: username `demo`, password `demo123`.
- On the assessment page, choose a synthetic sample case and click **Fill form**.
- Press **Get risk result** to see the risk level and reasons.
- Press **History** to review saved demo assessments.

Run the automated checks:

```powershell
python -m unittest discover -s tests -v
```

Expected result: `Ran 10 tests ... OK`.

## Short test checklist (manual)

- [ ] Home page loads and shows Continue as Guest.
- [ ] Guest button opens the form, result flow, and history with no login.
- [ ] Sample case 1 (fever + cough) gives Medium risk with visible reasons.
- [ ] Sample case 2 (low oxygen + chest pain) gives High risk and "urgent care today".
- [ ] Sample case 3 (mild symptoms) gives Low risk.
- [ ] Every result page shows the "doctor or nurse makes the final decision" note.
- [ ] A submitted assessment appears in History and opens again correctly.
- [ ] Only synthetic codes such as SYN-001 are used; no real patient data entered.
- [ ] Automated checks pass: `python -m unittest discover -s tests -v`.

## Safety and data notes

- The thresholds in `rules.py` are a simple demo heuristic and need clinical
  review before any real use. [CHECK]
- Do not enter real patient data. The demo stores entries locally in
  `data/health_digital.db` with no encryption and no access control.
- Delete `data/health_digital.db` to reset the demo.
