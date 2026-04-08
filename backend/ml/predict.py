"""
PharmaShield AI - ML Prediction Engine
Imported by app.py to score drug interaction risk.
"""

import pickle
import json
import os
import numpy as np
from itertools import combinations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
META_PATH = os.path.join(BASE_DIR, "meta.json")

# ── Load model once at import time ────────────────────────────────────────────
_model = None
_meta = None

def _load():
    global _model, _meta
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "ML model not found. Run: python ml/train_model.py"
            )
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        with open(META_PATH, "r") as f:
            _meta = json.load(f)

def _build_features(drug1, drug2, gender, conditions, qty1, qty2):
    """Build the same feature vector as used in training."""
    d1 = abs(hash(drug1.lower().strip())) % 10000
    d2 = abs(hash(drug2.lower().strip())) % 10000
    drug_pair_hash = abs(hash(tuple(sorted([drug1.lower(), drug2.lower()])))) % 10000

    gender_enc = 1 if str(gender).lower() in ["male", "m"] else 0

    cond_list = _meta["condition_list"]
    cond_vector = [
        1 if c in [x.lower().replace(" ", "_") for x in conditions] else 0
        for c in cond_list
    ]

    qty1 = float(qty1) if qty1 else 1.0
    qty2 = float(qty2) if qty2 else 1.0
    qty_ratio = qty1 / (qty2 + 1e-6)
    combined_qty = qty1 + qty2

    return [d1, d2, drug_pair_hash, gender_enc] + cond_vector + [
        qty1, qty2, round(qty_ratio, 4), combined_qty
    ]


def predict_interactions(drugs_data, gender, conditions):
    """
    Main prediction function called from app.py.

    Parameters
    ----------
    drugs_data : list of dict
        [{"name": "Warfarin", "quantity": 2}, {"name": "Aspirin", "quantity": 1}, ...]
    gender : str
        "male" or "female"
    conditions : list of str
        Patient medical conditions e.g. ["diabetes", "hypertension"]

    Returns
    -------
    dict with keys:
        overall_risk  : str  ("Low" / "Moderate" / "High" / "Critical")
        overall_score : int  (0–3)
        confidence    : float (0–1)
        pairs         : list of per-pair results
        ml_used       : bool
    """
    _load()

    severity_labels = _meta["severity_labels"]  # ["Low", "Moderate", "High", "Critical"]
    pairs_result = []
    max_score = 0
    max_confidence = 0.0

    drug_pairs = list(combinations(drugs_data, 2))

    if not drug_pairs:
        return {
            "overall_risk": "Low",
            "overall_score": 0,
            "confidence": 0.95,
            "pairs": [],
            "ml_used": True
        }

    for d1, d2 in drug_pairs:
        feats = _build_features(
            d1["name"], d2["name"],
            gender, conditions,
            d1.get("quantity", 1), d2.get("quantity", 1)
        )
        X = np.array([feats], dtype=float)

        pred_label = int(_model.predict(X)[0])
        proba = _model.predict_proba(X)[0]
        confidence = float(proba[pred_label])

        # Quantity modifier: high combined quantity → bump risk slightly
        combined_qty = float(d1.get("quantity", 1)) + float(d2.get("quantity", 1))
        if combined_qty > 6 and pred_label < 3:
            pred_label = min(pred_label + 1, 3)
            confidence = max(confidence * 0.85, 0.5)

        pairs_result.append({
            "drug1": d1["name"],
            "drug2": d2["name"],
            "risk_score": pred_label,
            "risk_label": severity_labels[pred_label],
            "confidence": round(confidence, 3),
            "qty1": d1.get("quantity", 1),
            "qty2": d2.get("quantity", 1),
            "probabilities": {
                severity_labels[i]: round(float(p), 3)
                for i, p in enumerate(proba)
            }
        })

        if pred_label > max_score or (pred_label == max_score and confidence > max_confidence):
            max_score = pred_label
            max_confidence = confidence

    return {
        "overall_risk": severity_labels[max_score],
        "overall_score": max_score,
        "confidence": round(max_confidence, 3),
        "pairs": pairs_result,
        "ml_used": True
    }


def is_model_ready():
    """Returns True if trained model file exists."""
    return os.path.exists(MODEL_PATH) and os.path.exists(META_PATH)
