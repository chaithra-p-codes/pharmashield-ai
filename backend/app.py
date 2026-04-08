"""
PharmaShield AI - Flask Backend
ML model handles risk scoring; Google Gemini handles explanation.
"""
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json

import google.generativeai as genai

# ── ML module import ───────────────────────────────────────────────────────────
from ml.predict import predict_interactions, is_model_ready

app = Flask(__name__)
CORS(app)

# ── Configure Gemini ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        print("✅ Gemini AI loaded successfully.")
    except Exception as e:
        print(f"⚠️ Gemini setup failed: {e}")
else:
    print("⚠️ GEMINI_API_KEY not found. Will use fallback explanation.")

# ── Load interactions.json ─────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(BASE_DIR, "interactions.json"), "r") as f:
        INTERACTIONS_DB = json.load(f)["interactions"]
    print("✅ interactions.json loaded.")
except Exception as e:
    print(f"⚠️ Could not load interactions.json: {e}")
    INTERACTIONS_DB = []

# ── Risk label mapping (ML → legacy UI severity) ──────────────────────────────
# ML returns: "Critical" / "High" / "Moderate" / "Low"
# Legacy UI expects: "dangerous" / "moderate" / "safe"
ML_TO_SEVERITY = {
    "Critical": "dangerous",
    "High":     "dangerous",
    "Moderate": "moderate",
    "Low":      "safe"
}

# ML overall_risk → legacy overall_risk for frontend banner
ML_TO_OVERALL = {
    "Critical": "dangerous",
    "High":     "dangerous",
    "Moderate": "moderate",
    "Low":      "safe"
}


# ── Fallback Explanation ───────────────────────────────────────────────────────
def generate_fallback_explanation(medicines, gender, conditions, ml_result):
    """Generate a meaningful explanation without AI."""
    overall_risk = ml_result.get("overall_risk", "Low")   # ML label e.g. "High"
    pairs        = ml_result.get("pairs", [])
    confidence   = ml_result.get("confidence", 0) * 100

    med_names = ", ".join([m["name"] for m in medicines])

    patient_note = ""
    if gender and gender != "unknown":
        patient_note += f" Given the patient's gender ({gender}),"
    if conditions:
        patient_note += f" and existing conditions ({', '.join(conditions)}),"
    if patient_note:
        patient_note += " extra caution is advised."

    # ── Critical / High ────────────────────────────────────────────────────────
    if overall_risk in ("Critical", "High"):
        high_pairs = [p for p in pairs if p.get("risk_label") in ("Critical", "High")]
        if high_pairs:
            top = high_pairs[0]
            # Pull rich data from interactions.json if available
            db_entry = _lookup_interaction(top.get("drug1", ""), top.get("drug2", ""))
            effect   = db_entry.get("effect", top.get("effect", "This combination may cause serious harm."))
            rec      = db_entry.get("recommendation", top.get("recommendation", "Please consult your doctor immediately."))
            msg = (
                f"A {overall_risk.lower()}-risk interaction was detected between "
                f"{top['drug1']} and {top['drug2']}. {effect}"
                f"{patient_note} {rec} "
                f"Do not continue this combination without medical advice. "
                f"⚕️ Always consult your doctor or pharmacist before changing medications."
            )
        else:
            msg = (
                f"A {overall_risk.lower()}-risk interaction was detected among: {med_names}."
                f"{patient_note} "
                f"Please stop taking these medicines together and consult your doctor immediately. "
                f"⚕️ Always consult your doctor or pharmacist before changing medications."
            )

    # ── Moderate ───────────────────────────────────────────────────────────────
    elif overall_risk == "Moderate":
        moderate_pairs = [p for p in pairs if p.get("risk_label") == "Moderate"]
        if moderate_pairs:
            top = moderate_pairs[0]
            db_entry = _lookup_interaction(top.get("drug1", ""), top.get("drug2", ""))
            effect   = db_entry.get("effect", top.get("effect", "This combination may cause side effects."))
            rec      = db_entry.get("recommendation", top.get("recommendation", "Discuss this with your healthcare provider."))
            msg = (
                f"A moderate interaction was detected between {top['drug1']} and {top['drug2']}. "
                f"{effect}{patient_note} {rec} "
                f"Monitor your symptoms closely. "
                f"⚕️ Always consult your doctor or pharmacist before changing medications."
            )
        else:
            msg = (
                f"A moderate interaction was detected among: {med_names}.{patient_note} "
                f"We recommend discussing this combination with your healthcare provider. "
                f"⚕️ Always consult your doctor or pharmacist before changing medications."
            )

    # ── Low / Safe ─────────────────────────────────────────────────────────────
    else:
        msg = (
            f"The medicines you entered ({med_names}) appear to carry low interaction risk "
            f"based on our analysis (confidence: {confidence:.0f}%).{patient_note} "
            f"No significant interactions were detected. "
            f"⚕️ Always consult your doctor or pharmacist before changing medications."
        )

    return msg


def _lookup_interaction(drug1, drug2):
    """Try to find enriched data from interactions.json for a pair."""
    d1, d2 = drug1.lower().strip(), drug2.lower().strip()
    for entry in INTERACTIONS_DB:
        e1 = entry.get("drug1", "").lower()
        e2 = entry.get("drug2", "").lower()
        if (e1 == d1 and e2 == d2) or (e1 == d2 and e2 == d1):
            return entry
    return {}


# ── Build Gemini Prompt ────────────────────────────────────────────────────────
def build_explanation_prompt(medicines, gender, conditions, ml_result):
    pairs_summary = "\n".join([
        f"  • {p['drug1']} + {p['drug2']}: {p['risk_label']} risk "
        f"(confidence {p['confidence'] * 100:.0f}%)"
        for p in ml_result.get("pairs", [])
    ]) or "  • No pair data available"

    meds_list = "\n".join(
        f"  • {m['name']}" + (f" — {m['dosage']}mg" if m.get('dosage') else "")
        for m in medicines
    )

    overall_risk  = ml_result.get("overall_risk", "Unknown")
    overall_score = ml_result.get("overall_score", "N/A")
    confidence    = ml_result.get("confidence", 0) * 100

    return f"""
You are a clinical pharmacist AI. An ML model has already scored the drug interactions.
Your job is to provide a clear, patient-friendly explanation that ACCURATELY reflects the ML risk level.

Patient Profile:
- Gender: {gender or 'Not specified'}
- Medical Conditions: {', '.join(conditions) if conditions else 'None reported'}
- Medicines:
{meds_list}

ML Risk Assessment:
- Overall Risk: {overall_risk} (score {overall_score}/3)
- Model Confidence: {confidence:.0f}%
- Pair-level breakdown:
{pairs_summary}

IMPORTANT: The overall risk is {overall_risk}. Your explanation MUST reflect this risk level.
- If risk is Critical or High: clearly warn about the danger, do NOT say the combination is safe.
- If risk is Moderate: advise caution and monitoring.
- If risk is Low: reassure but still advise consulting a doctor.

Instructions:
1. Briefly explain WHY each high-risk pair is dangerous (mechanism).
2. Mention if gender or conditions increase the risk for this patient.
3. Give 2-3 practical recommendations.
4. Use simple language. No markdown headers. Keep under 250 words.
5. End with: "⚕️ Always consult your doctor or pharmacist before changing medications."
""".strip()


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", ml_ready=is_model_ready())


@app.route("/api/check", methods=["POST"])
def check():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received. Please send a valid JSON body."}), 400

    medicines  = data.get("medicines", [])
    patient    = data.get("patient", {})
    gender     = patient.get("gender") or data.get("gender") or "unknown"
    conditions = patient.get("conditions") or data.get("conditions") or []
    age        = patient.get("age")
    weight     = patient.get("weight")

    if len(medicines) < 2:
        return jsonify({"error": "Please enter at least 2 medicines to check interactions."}), 400

    # ── Read drugs[] from frontend (contains actual dosage in mg) ──────────────
    drugs_payload = data.get("drugs", [])
    dosage_lookup = {
        d["name"].lower(): int(d.get("quantity", 1) or 1)
        for d in drugs_payload
        if d.get("name")
    }

    drugs_for_ml = [
        {
            "name":     m["name"],
            "quantity": dosage_lookup.get(m["name"].lower(), 1)
        }
        for m in medicines
    ]

    print(f"💊 Drugs for ML: {drugs_for_ml}")

    # ── Step 1: ML risk scoring ────────────────────────────────────────────────
    try:
        ml_result = predict_interactions(drugs_for_ml, gender, conditions)
        print(f"✅ ML result: {ml_result.get('overall_risk')} | confidence: {ml_result.get('confidence')}")
    except FileNotFoundError as e:
        print(f"❌ ML model not found: {e}")
        ml_result = {
            "overall_risk":  "Low",
            "overall_score": 0,
            "confidence":    0,
            "pairs":         [],
            "ml_used":       False,
            "error":         str(e)
        }
    except Exception as e:
        print(f"❌ ML prediction error: {e}")
        ml_result = {
            "overall_risk":  "Low",
            "overall_score": 0,
            "confidence":    0,
            "pairs":         [],
            "ml_used":       False,
            "error":         str(e)
        }

    # ── Enrich ML pairs with interactions.json data ────────────────────────────
    for pair in ml_result.get("pairs", []):
        db_entry = _lookup_interaction(pair.get("drug1", ""), pair.get("drug2", ""))
        if db_entry:
            pair.setdefault("effect",         db_entry.get("effect", "Interaction detected by ML model."))
            pair.setdefault("recommendation", db_entry.get("recommendation", "Consult your pharmacist."))
            pair.setdefault("mechanism",      db_entry.get("mechanism", ""))
            # Override risk_label with DB severity only if DB says it's more severe
            db_severity_rank = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
            ml_severity_rank = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
            db_sev  = db_entry.get("severity", "").lower()
            ml_sev  = pair.get("risk_label", "Low")
            if db_severity_rank.get(db_sev, 0) > ml_severity_rank.get(ml_sev, 0):
                # DB says more severe — trust DB
                db_to_ml_label = {"low": "Low", "moderate": "Moderate", "high": "High", "critical": "Critical"}
                pair["risk_label"] = db_to_ml_label.get(db_sev, ml_sev)
        else:
            pair.setdefault("effect",         "Interaction detected by ML model.")
            pair.setdefault("recommendation", "Consult your pharmacist.")

    # Recalculate overall_risk after DB enrichment
    if ml_result.get("pairs"):
        severity_rank = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
        top_pair = max(ml_result["pairs"], key=lambda p: severity_rank.get(p.get("risk_label", "Low"), 0))
        ml_result["overall_risk"]  = top_pair["risk_label"]
        ml_result["overall_score"] = severity_rank.get(top_pair["risk_label"], 0)

    # ── Enrich medicines list with dosage ──────────────────────────────────────
    medicines_with_dosage = [
        {"name": m["name"], "dosage": dosage_lookup.get(m["name"].lower(), None)}
        for m in medicines
    ]

    # ── Step 2: AI Explanation (Gemini or Fallback) ────────────────────────────
    explanation = ""
    ai_source   = "fallback"

    if gemini_model:
        try:
            prompt   = build_explanation_prompt(medicines_with_dosage, gender, conditions, ml_result)
            response = gemini_model.generate_content(prompt)

            if response and response.text and response.text.strip():
                explanation = response.text.strip()
                ai_source   = "gemini"
                print("✅ Gemini explanation generated successfully.")
            else:
                print("⚠️ Gemini returned empty response. Using fallback.")
                explanation = generate_fallback_explanation(medicines_with_dosage, gender, conditions, ml_result)
        except Exception as e:
            print(f"⚠️ Gemini error: {e} — switching to fallback.")
            explanation = generate_fallback_explanation(medicines_with_dosage, gender, conditions, ml_result)
    else:
        print("⚠️ Gemini not configured. Using fallback explanation.")
        explanation = generate_fallback_explanation(medicines_with_dosage, gender, conditions, ml_result)

    # ── Step 3: Build interactions list (ML pairs → legacy severity) ───────────
    pairs        = ml_result.get("pairs", [])
    ml_risk_raw  = ml_result.get("overall_risk", "Low")   # e.g. "High"
    overall_risk = ML_TO_OVERALL.get(ml_risk_raw, "safe") # e.g. "dangerous"

    interactions = []
    for p in pairs:
        ml_label = p.get("risk_label", "Low")
        severity = ML_TO_SEVERITY.get(ml_label, "moderate")
        interactions.append({
            "drug1":          p.get("drug1", ""),
            "drug2":          p.get("drug2", ""),
            "severity":       severity,
            "effect":         p.get("effect", "Interaction detected by ML model."),
            "recommendation": p.get("recommendation", "Consult your pharmacist."),
            "dosage_warning": p.get("dosage_warning", "")
        })

    return jsonify({
        "overall_risk":        overall_risk,
        "interactions_found":  len([i for i in interactions if i["severity"] in ("dangerous", "moderate")]),
        "interactions":        interactions,
        "medicines_checked":   [m["name"] for m in medicines],
        "total_pairs_checked": len(pairs),
        "ai_explanation":      explanation,
        "ai_source":           ai_source,
        "ml_result":           ml_result,
        "patient": {
            "age":        age,
            "weight":     weight,
            "gender":     gender,
            "conditions": conditions
        }
    })


# ── Legacy route ───────────────────────────────────────────────────────────────
@app.route("/api/check-interactions", methods=["POST"])
def check_interactions_legacy():
    return check()


@app.route("/api/medicines", methods=["GET"])
def get_medicines():
    names = list({entry.get("drug1") for entry in INTERACTIONS_DB}
               | {entry.get("drug2") for entry in INTERACTIONS_DB})
    names = sorted([n for n in names if n])
    return jsonify({"medicines": names})


@app.route("/api/model-status", methods=["GET"])
def model_status():
    ready = is_model_ready()
    return jsonify({
        "ml_ready": ready,
        "message":  "Model is ready" if ready else "Run: python ml/train_model.py"
    })


if __name__ == "__main__":
    if not is_model_ready():
        print("⚠️  ML model not found. Run: python ml/train_model.py")
    else:
        print("✅ ML model loaded and ready.")
    app.run(debug=True, port=5000)
