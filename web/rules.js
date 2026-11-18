export const SAFETY_NOTE =
  "This tool gives a simple triage hint only. It is not a diagnosis. A doctor or nurse makes the final decision.";

export const RECOMMENDATIONS = {
  High: "Seek urgent care today. Call your local emergency number or go to the nearest emergency service.",
  Medium: "Contact a doctor, nurse, or clinic within 24 hours. Watch for worse breathing, chest pain, confusion, or fainting.",
  Low: "Self-care and monitor. Repeat this check in 2 days, or sooner if the patient gets worse.",
};

export function assess(input) {
  const symptoms = input.symptoms || [];
  const high = [];
  const medium = [];

  if (input.spo2 < 92) high.push(`Oxygen level is very low (SpO2 ${input.spo2}%).`);
  else if (input.spo2 <= 94) medium.push(`Oxygen level is slightly low (SpO2 ${input.spo2}%).`);

  if (input.respiratory_rate >= 30) high.push(`Breathing rate is very high (${input.respiratory_rate} per minute).`);
  else if (input.respiratory_rate <= 8) high.push(`Breathing rate is very low (${input.respiratory_rate} per minute).`);
  else if (input.respiratory_rate >= 22) medium.push(`Breathing rate is above the usual range (${input.respiratory_rate} per minute).`);

  if (input.systolic_bp < 90) high.push(`Systolic blood pressure is low (${input.systolic_bp} mmHg).`);

  if (input.heart_rate >= 130 || input.heart_rate <= 45) high.push(`Heart rate is outside the usual range (${input.heart_rate} bpm).`);
  else if (input.heart_rate >= 110 || input.heart_rate <= 50) medium.push(`Heart rate is near the edge of the usual range (${input.heart_rate} bpm).`);

  if (symptoms.includes("chest_pain")) high.push("Chest pain is reported.");
  if (symptoms.includes("confusion")) high.push("Confusion is reported.");
  if (symptoms.includes("shortness_of_breath") && symptoms.includes("fever")) high.push("Shortness of breath together with fever is reported.");
  if (input.temperature_c >= 39 && input.duration_days >= 3) high.push("High fever has lasted 3 or more days.");

  if (input.temperature_c >= 38 && input.temperature_c <= 38.9) medium.push(`Fever is present (${input.temperature_c} C).`);
  if (input.duration_days >= 5 && symptoms.includes("cough")) medium.push("Cough has lasted 5 or more days.");
  if (input.age >= 65 && (symptoms.includes("weakness") || symptoms.includes("fever"))) medium.push("Older patient with weakness or fever.");
  if (symptoms.length >= 2) medium.push("More than one symptom is present.");

  let risk = "Low";
  let reasons = ["No danger signs were found in the data you entered."];
  if (high.length) {
    risk = "High";
    reasons = high.slice(0, 4);
  } else if (medium.length) {
    risk = "Medium";
    reasons = medium.slice(0, 4);
  }

  return { risk, reasons, recommendation: RECOMMENDATIONS[risk], safety_note: SAFETY_NOTE };
}
