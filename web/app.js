import { assess } from "./rules.js";

const SAMPLES = [
  {
    id: "SYN-001",
    label: "Sample 1: fever and cough",
    inputs: { age: 34, temperature_c: 38.4, heart_rate: 96, respiratory_rate: 20, systolic_bp: 118, spo2: 97, symptoms: ["fever", "cough"], duration_days: 2 },
  },
  {
    id: "SYN-002",
    label: "Sample 2: low oxygen and chest pain",
    inputs: { age: 61, temperature_c: 38.8, heart_rate: 118, respiratory_rate: 28, systolic_bp: 104, spo2: 90, symptoms: ["fever", "cough", "shortness_of_breath", "chest_pain"], duration_days: 1 },
  },
  {
    id: "SYN-003",
    label: "Sample 3: mild symptoms",
    inputs: { age: 25, temperature_c: 36.8, heart_rate: 74, respiratory_rate: 16, systolic_bp: 120, spo2: 99, symptoms: ["cough"], duration_days: 1 },
  },
];

const STORAGE_KEY = "signal_to_support_assessments";
const el = (id) => document.getElementById(id);
const app = el("app");
const flashBox = el("flash");
const statusChip = el("status-chip");

let records = [];
try {
  records = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
} catch (_error) {
  records = [];
}

function flash(message) {
  flashBox.textContent = message;
  flashBox.hidden = false;
}

function unlock(mode) {
  sessionStorage.setItem("signal_access", mode);
  app.hidden = false;
  statusChip.textContent = mode === "guest" ? "Guest mode: all features on" : "Demo user: demo";
  statusChip.className = "chip chip-guest";
  el("sign-out").hidden = false;
  flash(mode === "guest" ? "Guest mode is on. All features are unlocked." : "Signed in with the demo account.");
  renderHistory();
  el("home").scrollIntoView({ behavior: "smooth" });
}

function readInputs() {
  const symptoms = Array.from(document.querySelectorAll('input[name="symptoms"]:checked')).map((box) => box.value);
  return {
    age: Number(el("age").value),
    temperature_c: Number(el("temperature_c").value),
    heart_rate: Number(el("heart_rate").value),
    respiratory_rate: Number(el("respiratory_rate").value),
    systolic_bp: Number(el("systolic_bp").value),
    spo2: Number(el("spo2").value),
    duration_days: Number(el("duration_days").value),
    symptoms,
  };
}

function renderResult(record) {
  const { result, inputs } = record;
  el("result-code").textContent = record.patient_code;
  el("result-time").textContent = `Recorded ${record.created_at}`;
  const badge = el("risk-badge");
  badge.textContent = `${result.risk.toUpperCase()} RISK`;
  badge.className = `badge risk-${result.risk.toLowerCase()}`;
  el("risk-recommendation").textContent = result.recommendation;
  el("risk-signal").textContent = `Signals: ${inputs.temperature_c} C, HR ${inputs.heart_rate} bpm, RR ${inputs.respiratory_rate}/min, BP ${inputs.systolic_bp} mmHg, SpO2 ${inputs.spo2}%.`;
  const list = el("risk-reasons");
  list.replaceChildren();
  result.reasons.forEach((reason) => {
    const item = document.createElement("li");
    item.textContent = reason;
    list.appendChild(item);
  });
  el("result-section").hidden = false;
}

function renderHistory() {
  const body = el("history-body");
  body.replaceChildren();
  if (!records.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.textContent = "No assessments yet. Create one above.";
    row.appendChild(cell);
    body.appendChild(row);
    return;
  }
  records.slice(0, 20).forEach((record) => {
    const row = document.createElement("tr");
    [String(record.id), record.patient_code, record.created_at, record.result.risk].forEach((value, index) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      if (index === 3) cell.className = `risk-${value.toLowerCase()}`;
      row.appendChild(cell);
    });
    const action = document.createElement("td");
    const button = document.createElement("button");
    button.className = "link-button";
    button.textContent = "Open";
    button.addEventListener("click", () => {
      renderResult(record);
      el("result-section").scrollIntoView({ behavior: "smooth" });
    });
    action.appendChild(button);
    row.appendChild(action);
    body.appendChild(row);
  });
}

el("guest-button").addEventListener("click", () => unlock("guest"));
el("guest-button-2").addEventListener("click", () => unlock("guest"));

el("demo-login").addEventListener("submit", (event) => {
  event.preventDefault();
  if (el("username").value.trim() === "demo" && el("password").value === "demo123") {
    unlock("demo");
  } else {
    flash("Those demo details are not correct. Try demo / demo123, or continue as guest.");
  }
});

el("sign-out").addEventListener("click", () => {
  sessionStorage.removeItem("signal_access");
  app.hidden = true;
  el("result-section").hidden = true;
  statusChip.textContent = "Not signed in";
  statusChip.className = "chip";
  el("sign-out").hidden = true;
  flash("You have left the session.");
});

document.querySelectorAll("[data-requires-access]").forEach((link) => {
  link.addEventListener("click", () => {
    if (app.hidden) unlock("guest");
  });
});

el("sample_select").replaceChildren(new Option("Choose a sample...", ""));
SAMPLES.forEach((sample) => el("sample_select").add(new Option(sample.label, sample.id)));
el("load_sample").addEventListener("click", () => {
  const sample = SAMPLES.find((item) => item.id === el("sample_select").value);
  if (!sample) return;
  el("patient_code").value = sample.id;
  ["age", "temperature_c", "heart_rate", "respiratory_rate", "systolic_bp", "spo2", "duration_days"].forEach((key) => {
    el(key).value = sample.inputs[key];
  });
  document.querySelectorAll('input[name="symptoms"]').forEach((box) => {
    box.checked = sample.inputs.symptoms.includes(box.value);
  });
  flash(`${sample.label} loaded.`);
});

el("assess-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const inputs = readInputs();
  const values = Object.values(inputs).filter((value) => !Array.isArray(value));
  if (values.some((value) => !Number.isFinite(value)) || inputs.age < 0 || inputs.age > 120 || inputs.spo2 < 0 || inputs.spo2 > 100) {
    flash("Please check every field. Age must be 0-120 and SpO2 must be 0-100.");
    return;
  }
  const result = assess(inputs);
  const record = {
    id: Date.now(),
    patient_code: (el("patient_code").value.trim() || "GUEST").slice(0, 40),
    created_at: new Date().toISOString().slice(0, 19).replace("T", " "),
    inputs,
    result,
  };
  records.unshift(record);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
  renderResult(record);
  renderHistory();
  el("result-section").scrollIntoView({ behavior: "smooth" });
});

const savedAccess = sessionStorage.getItem("signal_access");
if (savedAccess === "guest" || savedAccess === "demo") {
  app.hidden = false;
  statusChip.textContent = savedAccess === "guest" ? "Guest mode: all features on" : "Demo user: demo";
  statusChip.className = "chip chip-guest";
  el("sign-out").hidden = false;
  renderHistory();
} else {
  app.hidden = true;
  el("sign-out").hidden = true;
}
