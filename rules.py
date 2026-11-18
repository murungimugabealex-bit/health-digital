SYMPTOM_LABELS = {
    "fever": "Fever",
    "cough": "Cough",
    "shortness_of_breath": "Shortness of breath",
    "chest_pain": "Chest pain",
    "weakness": "Weakness",
    "confusion": "Confusion",
}

SAFETY_NOTE = (
    "This tool gives a simple triage hint only. It is not a diagnosis. "
    "A doctor or nurse makes the final decision."
)

RECOMMENDATIONS = {
    "High": (
        "Seek urgent care today. Call your local emergency number or go to the "
        "nearest emergency service."
    ),
    "Medium": (
        "Contact a doctor, nurse, or clinic within 24 hours. Watch for worse "
        "breathing, chest pain, confusion, or fainting."
    ),
    "Low": (
        "Self-care and monitor. Repeat this check in 2 days, or sooner if the "
        "patient gets worse."
    ),
}


def assess(age, temperature_c, heart_rate, respiratory_rate, systolic_bp, spo2,
           symptoms, duration_days):
    symptoms = list(symptoms or [])
    high = []
    medium = []

    if spo2 < 92:
        high.append("Oxygen level is very low (SpO2 {}%).".format(spo2))
    elif spo2 <= 94:
        medium.append("Oxygen level is slightly low (SpO2 {}%).".format(spo2))

    if respiratory_rate >= 30:
        high.append("Breathing rate is very high ({} per minute).".format(respiratory_rate))
    elif respiratory_rate <= 8:
        high.append("Breathing rate is very low ({} per minute).".format(respiratory_rate))
    elif respiratory_rate >= 22:
        medium.append("Breathing rate is above the usual range ({} per minute).".format(respiratory_rate))

    if systolic_bp < 90:
        high.append("Systolic blood pressure is low ({} mmHg).".format(systolic_bp))

    if heart_rate >= 130 or heart_rate <= 45:
        high.append("Heart rate is outside the usual range ({} bpm).".format(heart_rate))
    elif heart_rate >= 110 or heart_rate <= 50:
        medium.append("Heart rate is near the edge of the usual range ({} bpm).".format(heart_rate))

    if "chest_pain" in symptoms:
        high.append("Chest pain is reported.")
    if "confusion" in symptoms:
        high.append("Confusion is reported.")
    if "shortness_of_breath" in symptoms and "fever" in symptoms:
        high.append("Shortness of breath together with fever is reported.")
    if temperature_c >= 39 and duration_days >= 3:
        high.append("High fever has lasted 3 or more days.")

    if 38.0 <= temperature_c <= 38.9:
        medium.append("Fever is present ({} C).".format(temperature_c))
    if duration_days >= 5 and "cough" in symptoms:
        medium.append("Cough has lasted 5 or more days.")
    if age >= 65 and ("weakness" in symptoms or "fever" in symptoms):
        medium.append("Older patient with weakness or fever.")
    if len(symptoms) >= 2:
        medium.append("More than one symptom is present.")

    if high:
        risk = "High"
        reasons = high[:4]
    elif medium:
        risk = "Medium"
        reasons = medium[:4]
    else:
        risk = "Low"
        reasons = ["No danger signs were found in the data you entered."]

    return {
        "risk": risk,
        "reasons": reasons,
        "recommendation": RECOMMENDATIONS[risk],
        "safety_note": SAFETY_NOTE,
    }
