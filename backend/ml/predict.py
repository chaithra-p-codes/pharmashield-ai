"""
PharmaShield AI - ML Prediction Engine
Imported by app.py to score drug interaction risk.
"""

import pickle
import json
import os
import hashlib
import numpy as np
from itertools import combinations

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
META_PATH  = os.path.join(BASE_DIR, "meta.json")

# ── Load model once at import time ────────────────────────────────────────────
_model = None
_meta  = None


def _stable_hash(s: str) -> int:
    """
    Deterministic hash stable across Python processes and PYTHONHASHSEED values.
    Uses MD5 (not for security — just for stable integer fingerprinting of strings).
    """
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % 10000


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
        print(f" ML model loaded. Features expected: {_meta.get('feature_count')}")


def _build_features(drug1, drug2, gender, conditions, qty1_mg, qty2_mg):
    """
    Build the EXACT same feature vector used in training.
    Order: [drug1_hash, drug2_hash, drug_pair_hash, gender_enc,
            *conditions_onehot,
            qty1_norm, qty2_norm, qty_ratio_capped_norm, combined_qty_norm]
    """
    # FIX: Read normalization constants from meta (same values as training)
    MAX_DOSE      = float(_meta.get("max_dose", 1000.0))
    MAX_QTY_RATIO = float(_meta.get("max_qty_ratio", 10.0))

    # FIX: Use stable hashlib.md5 instead of Python's built-in hash()
    # Python's hash() is randomized per-process via PYTHONHASHSEED,
    # so drug hashes during training differ from hashes during prediction —
    # making drug identity features completely meaningless to the model.
    d1_key         = drug1.lower().strip()
    d2_key         = drug2.lower().strip()
    pair_key       = "_".join(sorted([d1_key, d2_key]))

    d1             = _stable_hash(d1_key)
    d2             = _stable_hash(d2_key)
    drug_pair_hash = _stable_hash(pair_key)

    gender_enc     = 1 if str(gender).lower() in ["male", "m"] else 0

    cond_list   = _meta["condition_list"]
    cond_vector = [
        1 if c in [x.lower().replace(" ", "_") for x in conditions] else 0
        for c in cond_list
    ]

    qty1 = float(qty1_mg) if qty1_mg else 1.0
    qty2 = float(qty2_mg) if qty2_mg else 1.0

    # Normalize exactly as training did
    qty1_norm     = min(qty1 / MAX_DOSE, 1.0)
    qty2_norm     = min(qty2 / MAX_DOSE, 1.0)
    raw_ratio     = qty1 / (qty2 + 1e-6)
    qty_ratio     = min(raw_ratio, MAX_QTY_RATIO) / MAX_QTY_RATIO  # normalized 0–1
    combined_norm = min((qty1 + qty2) / (2 * MAX_DOSE), 1.0)

    return (
        [d1, d2, drug_pair_hash, gender_enc]
        + cond_vector
        + [qty1_norm, qty2_norm, round(qty_ratio, 4), combined_norm]
    )


def predict_interactions(drugs_data, gender, conditions):
    """
    Main prediction function called from app.py.

    Parameters
    ----------
    drugs_data : list of dict
        [{"name": "Warfarin", "quantity": 500}, ...]  quantity = dosage in mg
    gender : str
        "male" or "female"
    conditions : list of str
        e.g. ["diabetes", "hypertension"]

    Returns
    -------
    dict with keys:
        overall_risk  : str   ("Low" / "Moderate" / "High" / "Critical")
        overall_score : int   (0–3)
        confidence    : float (0.0–1.0)
        pairs         : list of per-pair results
        ml_used       : bool
    """
    _load()

    severity_labels = _meta["severity_labels"]   # ["Low","Moderate","High","Critical"]
    pairs_result    = []
    max_score       = 0
    max_confidence  = 0.0

    drug_pairs = list(combinations(drugs_data, 2))

    if not drug_pairs:
        return {
            "overall_risk":  "Low",
            "overall_score": 0,
            "confidence":    0.95,
            "pairs":         [],
            "ml_used":       True,
        }

    for d1, d2 in drug_pairs:
        feats = _build_features(
            d1["name"], d2["name"],
            gender, conditions,
            d1.get("quantity", 1),   # quantity = mg dosage
            d2.get("quantity", 1),
        )
        X = np.array([feats], dtype=float)

        pred_label = int(_model.predict(X)[0])
        proba      = _model.predict_proba(X)[0]
        confidence = float(proba[pred_label])

        pairs_result.append({
            "drug1":       d1["name"],
            "drug2":       d2["name"],
            "risk_score":  pred_label,
            "risk_label":  severity_labels[pred_label],
            "confidence":  round(confidence, 3),
            "qty1":        d1.get("quantity", 1),
            "qty2":        d2.get("quantity", 1),
            "probabilities": {
                severity_labels[i]: round(float(p), 3)
                for i, p in enumerate(proba)
            },
        })

        if pred_label > max_score or (
            pred_label == max_score and confidence > max_confidence
        ):
            max_score      = pred_label
            max_confidence = confidence

    return {
        "overall_risk":  severity_labels[max_score],
        "overall_score": max_score,
        "confidence":    round(max_confidence, 3),
        "pairs":         pairs_result,
        "ml_used":       True,
    }


def is_model_ready():
    """Returns True if trained model file exists."""
    return os.path.exists(MODEL_PATH) and os.path.exists(META_PATH)
