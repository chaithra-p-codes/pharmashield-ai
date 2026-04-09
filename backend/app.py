"""
PharmaShield AI — Flask Backend
- Groq (Llama 3) generates patient-specific explanation
- ML scores interactions; DB enriches with effect/recommendation text
- Falls back gracefully if Groq fails
- Stats, banner and cards are always consistent
"""

from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json

# ── Groq SDK ───────────────────────────────────────────────────────────────────
from groq import Groq

# ── ML module ──────────────────────────────────────────────────────────────────
from ml.predict import predict_interactions, is_model_ready

app = Flask(__name__)
CORS(app)

# ── Configure Groq ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client  = None

if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq AI (Llama 3) loaded successfully.")
    except Exception as e:
        print(f"⚠️  Groq setup failed: {e}")
        groq_client = None
else:
    print("⚠️  GROQ_API_KEY not found in .env — will use fallback explanation.")

# ── Load interactions.json ─────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(BASE_DIR, "interactions.json"), "r") as f:
        INTERACTIONS_DB = json.load(f)["interactions"]
    print(f"✅ interactions.json loaded — {len(INTERACTIONS_DB)} entries.")
except Exception as e:
    print(f"⚠️  Could not load interactions.json: {e}")
    INTERACTIONS_DB = []

# ── Severity mappings ──────────────────────────────────────────────────────────
ML_TO_SEVERITY = {
    "Critical": "dangerous",
    "High":     "dangerous",
    "Moderate": "moderate",
    "Low":      "safe",
}

ML_TO_OVERALL = {
    "Critical": "dangerous",
    "High":     "dangerous",
    "Moderate": "moderate",
    "Low":      "safe",
    "Unknown":  "safe",
}

SEVERITY_RANK = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}

#  HELPER — look up a pair in interactions.json (text enrichment only)
def _lookup_interaction(drug1: str, drug2: str) -> dict:
    d1, d2 = drug1.lower().strip(), drug2.lower().strip()
    for entry in INTERACTIONS_DB:
        e1 = entry.get("drug1", "").lower()
        e2 = entry.get("drug2", "").lower()
        if (e1 == d1 and e2 == d2) or (e1 == d2 and e2 == d1):
            return entry
    return {}

#  FALLBACK EXPLANATION
def generate_fallback_explanation(medicines: list, gender: str,
                                  conditions: list, ml_result: dict) -> str:
    overall_risk = ml_result.get("overall_risk", "Low")
    pairs        = ml_result.get("pairs", [])
    confidence   = ml_result.get("confidence", 0) * 100
    med_names    = ", ".join(m["name"] for m in medicines)

    parts = []
    if gender and gender not in ("unknown", "other"):
        parts.append(f"gender ({gender})")
    if conditions:
        parts.append(f"existing conditions ({', '.join(conditions)})")
    patient_note = (
        f" Given the patient's {' and '.join(parts)}, extra caution is advised."
        if parts else ""
    )

    if overall_risk in ("Critical", "High"):
        top_pairs = [p for p in pairs if p.get("risk_label") in ("Critical", "High")]
        if top_pairs:
            top    = top_pairs[0]
            db     = _lookup_interaction(top.get("drug1", ""), top.get("drug2", ""))
            effect = db.get("effect") or "This combination may cause serious harm."
            rec    = db.get("recommendation") or "Please consult your doctor immediately."
            return (
                f"A {overall_risk.lower()}-risk interaction was detected between "
                f"{top['drug1']} and {top['drug2']}. {effect}"
                f"{patient_note} {rec} "
                "Do not continue this combination without medical advice. "
                "⚕️ Always consult your doctor or pharmacist before changing medications."
            )
        return (
            f"A {overall_risk.lower()}-risk interaction was detected among: {med_names}."
            f"{patient_note} Please stop taking these medicines together and consult "
            "your doctor immediately. "
            "⚕️ Always consult your doctor or pharmacist before changing medications."
        )

    if overall_risk == "Moderate":
        top_pairs = [p for p in pairs if p.get("risk_label") == "Moderate"]
        if top_pairs:
            top    = top_pairs[0]
            db     = _lookup_interaction(top.get("drug1", ""), top.get("drug2", ""))
            effect = db.get("effect") or "This combination may cause side effects."
            rec    = db.get("recommendation") or "Discuss this with your healthcare provider."
            return (
                f"A moderate interaction was detected between "
                f"{top['drug1']} and {top['drug2']}. "
                f"{effect}{patient_note} {rec} Monitor your symptoms closely. "
                "⚕️ Always consult your doctor or pharmacist before changing medications."
            )
        return (
            f"A moderate interaction was detected among: {med_names}.{patient_note} "
            "We recommend discussing this combination with your healthcare provider. "
            "⚕️ Always consult your doctor or pharmacist before changing medications."
        )

    return (
        f"The medicines you entered ({med_names}) appear to carry low interaction risk "
        f"based on our analysis (confidence: {confidence:.0f}%).{patient_note} "
        "No significant interactions were detected. "
        "⚕️ Always consult your doctor or pharmacist before changing medications."
    )

#  GROQ PROMPT BUILDER
def build_prompt(medicines: list, gender: str,
                 conditions: list, ml_result: dict) -> str:
    overall_risk  = ml_result.get("overall_risk", "Unknown")
    overall_score = ml_result.get("overall_score", "N/A")
    confidence    = ml_result.get("confidence", 0) * 100

    meds_list = "\n".join(
        f"  • {m['name']}" + (f" — {m['dosage']}mg" if m.get("dosage") else "")
        for m in medicines
    )

    pairs_summary = "\n".join(
        f"  • {p['drug1']} + {p['drug2']}: {p['risk_label']} risk "
        f"(confidence {p['confidence'] * 100:.0f}%)"
        + (f" — {p.get('effect', '')}" if p.get("effect") else "")
        for p in ml_result.get("pairs", [])
    ) or "  • No pair data available"

    return (
        "You are a clinical pharmacist AI. An ML model has already scored the drug "
        "interactions below. Write a clear, patient-friendly explanation that ACCURATELY "
        "reflects the ML risk level.\n\n"
        f"Patient Profile:\n"
        f"- Gender: {gender or 'Not specified'}\n"
        f"- Medical Conditions: {', '.join(conditions) if conditions else 'None reported'}\n"
        f"- Medicines:\n{meds_list}\n\n"
        f"ML Risk Assessment:\n"
        f"- Overall Risk: {overall_risk} (score {overall_score}/3)\n"
        f"- Model Confidence: {confidence:.0f}%\n"
        f"- Pair-level breakdown:\n{pairs_summary}\n\n"
        "STRICT RULES:\n"
        f"- Overall risk is {overall_risk}. Your explanation MUST match this level.\n"
        "- If Critical or High: clearly warn about danger. Do NOT say it is safe.\n"
        "- If Moderate: advise caution and monitoring.\n"
        "- If Low: reassure but still advise professional consultation.\n"
        "- Explain WHY each high-risk pair is dangerous (mechanism, plain language).\n"
        "- Mention how the patient's gender or conditions increase the risk, if relevant.\n"
        "- Give 2-3 practical, actionable recommendations.\n"
        "- No markdown, no bullet points, no headers. Plain paragraph text only.\n"
        "- Maximum 220 words.\n"
        "- Final sentence must be exactly: "
        "⚕️ Always consult your doctor or pharmacist before changing medications."
    )

#  GROQ API CALL
def call_groq(prompt: str):
    """Returns AI-generated text string, or None on failure."""
    try:
        print("🔄 Calling Groq API...")
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role":    "system",
                    "content": (
                        "You are a clinical pharmacist AI assistant. "
                        "Always respond in plain text, no markdown, no bullet points. "
                        "Be concise, accurate, and patient-friendly."
                    ),
                },
                {
                    "role":    "user",
                    "content": prompt,
                },
            ],
            max_tokens=400,
            temperature=0.3,
        )
        text = (response.choices[0].message.content or "").strip()
        print(f"✅ Groq response received ({len(text)} chars).")
        return text if text else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"⚠️  Groq API call failed: {e}")
        return None

#  ROUTES
@app.route("/")
def index():
    return render_template("index.html", ml_ready=is_model_ready())


@app.route("/api/check", methods=["POST"])
def check():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body received."}), 400

    # ── Parse request ──────────────────────────────────────────────────────────
    medicines  = data.get("medicines", [])
    patient    = data.get("patient", {})
    gender     = (patient.get("gender") or data.get("gender") or "unknown").strip().lower()
    conditions = patient.get("conditions") or data.get("conditions") or []
    age        = patient.get("age")
    weight     = patient.get("weight")

    if len(medicines) < 2:
        return jsonify({"error": "Please enter at least 2 medicines."}), 400

    # ── Build dosage lookup ────────────────────────────────────────────────────
    dosage_lookup = {}
    for d in data.get("drugs", []):
        name = (d.get("name") or "").lower().strip()
        if name:
            try:
                dosage_lookup[name] = max(1, int(d.get("quantity") or 1))
            except (ValueError, TypeError):
                dosage_lookup[name] = 1

    # ── Drugs list for ML (with real mg dosage) ────────────────────────────────
    drugs_for_ml = [
        {
            "name":     m["name"].lower().strip(),
            "quantity": dosage_lookup.get(m["name"].lower().strip(), 1),
        }
        for m in medicines if m.get("name")
    ]

    print(f"💊 Drugs for ML: {drugs_for_ml}")

    # ── Step 1: ML risk scoring ────────────────────────────────────────────────
    try:
        ml_result = predict_interactions(drugs_for_ml, gender, conditions)
        print(f"✅ ML: {ml_result.get('overall_risk')} | "
              f"conf: {ml_result.get('confidence'):.3f} | "
              f"pairs: {len(ml_result.get('pairs', []))}")
    except FileNotFoundError:
        print("❌ ML model not found — run: python ml/train_model.py")
        ml_result = {
            "overall_risk":  "Low",
            "overall_score": 0,
            "confidence":    0.0,
            "pairs":         [],
            "ml_used":       False,
            "error":         "Model not trained yet.",
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"❌ ML prediction error: {e}")
        ml_result = {
            "overall_risk":  "Low",
            "overall_score": 0,
            "confidence":    0.0,
            "pairs":         [],
            "ml_used":       False,
            "error":         str(e),
        }

    # ── Step 2: Enrich ML pairs from interactions.json ─────────────────────────
    for pair in ml_result.get("pairs", []):
        db = _lookup_interaction(pair.get("drug1", ""), pair.get("drug2", ""))
        if db:
            pair.setdefault("effect",         db.get("effect", "Interaction detected."))
            pair.setdefault("recommendation", db.get("recommendation", "Consult your pharmacist."))
            pair.setdefault("mechanism",      db.get("mechanism", ""))
            # FIX: DB severity override REMOVED — ML label stands as-is
        else:
            pair.setdefault("effect",         "Interaction detected by ML model.")
            pair.setdefault("recommendation", "Consult your pharmacist.")

    # FIX: Overall risk is purely from ML pairs — no DB interference
    if ml_result.get("pairs"):
        top_pair = max(
            ml_result["pairs"],
            key=lambda p: SEVERITY_RANK.get(p.get("risk_label", "Low"), 0)
        )
        ml_result["overall_risk"]  = top_pair["risk_label"]
        ml_result["overall_score"] = SEVERITY_RANK[top_pair["risk_label"]]

    # ── Medicines enriched with dosage (for Groq prompt) ──────────────────────
    medicines_enriched = [
        {
            "name":   m["name"].lower().strip(),
            "dosage": dosage_lookup.get(m["name"].lower().strip()),
        }
        for m in medicines if m.get("name")
    ]

    # ── Step 3: Generate explanation ───────────────────────────────────────────
    ai_source   = "fallback"
    explanation = ""

    if groq_client:
        prompt  = build_prompt(medicines_enriched, gender, conditions, ml_result)
        ai_text = call_groq(prompt)
        if ai_text:
            explanation = ai_text
            ai_source   = "groq"
            print("✅ Groq explanation set.")
        else:
            print("⚠️  Groq returned empty — using fallback.")
            explanation = generate_fallback_explanation(
                medicines_enriched, gender, conditions, ml_result
            )
    else:
        print("⚠️  Groq not configured — using fallback.")
        explanation = generate_fallback_explanation(
            medicines_enriched, gender, conditions, ml_result
        )

    # ── Step 4: Build interaction cards ───────────────────────────────────────
    pairs = ml_result.get("pairs", [])
    interactions_out = [
        {
            "drug1":          p.get("drug1", ""),
            "drug2":          p.get("drug2", ""),
            "severity":       ML_TO_SEVERITY.get(p.get("risk_label", "Low"), "safe"),
            "effect":         p.get("effect", "Interaction detected."),
            "recommendation": p.get("recommendation", "Consult your pharmacist."),
            "dosage_warning": p.get("dosage_warning", ""),
        }
        for p in pairs
    ]

    # ── Step 5: Counts from cards ──────────────────────────────────────────────
    n_dangerous  = sum(1 for i in interactions_out if i["severity"] == "dangerous")
    n_moderate   = sum(1 for i in interactions_out if i["severity"] == "moderate")
    overall_risk = ML_TO_OVERALL.get(ml_result.get("overall_risk", "Low"), "safe")

    print(f" Response — overall: {overall_risk} | "
          f"dangerous: {n_dangerous} | moderate: {n_moderate} | "
          f"ai_source: {ai_source}")

    return jsonify({
        "overall_risk":        overall_risk,
        "interactions_found":  n_dangerous + n_moderate,
        "total_pairs_checked": len(pairs),
        "medicines_checked":   [m["name"] for m in medicines_enriched],
        "interactions":        interactions_out,
        "ai_explanation":      explanation,
        "ai_source":           ai_source,
        "ml_result":           ml_result,
        "patient": {
            "age":        age,
            "weight":     weight,
            "gender":     gender,
            "conditions": conditions,
        },
    })


# ── Alias route (backward compat) ─────────────────────────────────────────────
@app.route("/api/check-interactions", methods=["POST"])
def check_interactions_legacy():
    return check()


@app.route("/api/medicines", methods=["GET"])
def get_medicines():
    """Return all unique drug names from interactions.json for autocomplete."""
    names = sorted({
        n for entry in INTERACTIONS_DB
        for n in (entry.get("drug1", ""), entry.get("drug2", ""))
        if n
    })
    return jsonify({"medicines": names})


@app.route("/api/model-status", methods=["GET"])
def model_status():
    ready = is_model_ready()
    return jsonify({
        "ml_ready": ready,
        "message":  "Model is ready" if ready else "Run: python ml/train_model.py",
    })

#  ENTRY POINT
if __name__ == "__main__":
    print(f"🔑 GROQ_API_KEY found: {bool(GROQ_API_KEY)}")
    if not is_model_ready():
        print("⚠️  ML model not found. Run: python ml/train_model.py")
    else:
        print("✅ ML model loaded and ready.")
    app.run(debug=True, port=5000, use_reloader=False)
