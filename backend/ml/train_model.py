"""
PharmaShield AI - ML Model Training Script
Run this once: python ml/train_model.py
It reads interactions.json and trains a risk classifier.
"""

import json
import pickle
import os
import hashlib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ── Load interactions.json ─────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "interactions.json"))
print("DEBUG PATH:", DATA_PATH)

with open(DATA_PATH, "r") as f:
    raw_data = json.load(f)

interactions = raw_data.get("interactions", raw_data)

# ── Constants (must match predict.py exactly) ─────────────────────────────────
SEVERITY_MAP = {"low": 0, "moderate": 1, "high": 2, "critical": 3}

CONDITION_LIST = [
    "diabetes", "hypertension", "kidney_disease", "liver_disease",
    "heart_disease", "asthma", "bleeding_disorder", "pregnancy",
    "elderly", "renal_impairment"
]

# Normalize dosage — real world mg values divided by MAX_DOSE
# Training will use normalized values; prediction must do the same
MAX_DOSE = 1000.0  # normalize all dosages to 0–1 range


def _stable_hash(s: str) -> int:
    """
    Deterministic hash stable across Python processes and PYTHONHASHSEED values.
    Uses MD5 (not for security — just for stable integer fingerprinting of strings).

    Python's built-in hash() is randomized per-process via PYTHONHASHSEED.
    This means a drug name like 'metformin' hashes to a different integer every
    time Python starts. The model trains on one set of integers and then receives
    completely different integers at prediction time — making drug identity features
    meaningless and causing systematic misclassification.
    """
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % 10000


def build_features(drug1, drug2, gender, conditions, qty1_mg, qty2_mg):
    """
    Returns a flat feature vector. Order must EXACTLY match predict.py.
    [drug1_hash, drug2_hash, drug_pair_hash, gender_enc,
     *conditions_onehot,
     qty1_norm, qty2_norm, qty_ratio_capped, combined_qty_norm]
    """
    # FIX: Use stable hashlib.md5 instead of Python's built-in hash()
    d1_key         = drug1.lower().strip()
    d2_key         = drug2.lower().strip()
    pair_key       = "_".join(sorted([d1_key, d2_key]))

    d1             = _stable_hash(d1_key)
    d2             = _stable_hash(d2_key)
    drug_pair_hash = _stable_hash(pair_key)

    gender_enc     = 1 if str(gender).lower() in ["male", "m"] else 0

    cond_vector = [
        1 if c in [x.lower().replace(" ", "_") for x in conditions] else 0
        for c in CONDITION_LIST
    ]

    # Normalize dosage to 0–1 using MAX_DOSE
    qty1_norm = min(float(qty1_mg) / MAX_DOSE, 1.0)
    qty2_norm = min(float(qty2_mg) / MAX_DOSE, 1.0)

    # Cap ratio to avoid extreme values like 500/5=100
    raw_ratio     = float(qty1_mg) / (float(qty2_mg) + 1e-6)
    qty_ratio     = min(raw_ratio, 10.0) / 10.0  # cap at 10, then normalize to 0–1

    combined_norm = min((float(qty1_mg) + float(qty2_mg)) / (2 * MAX_DOSE), 1.0)

    return (
        [d1, d2, drug_pair_hash, gender_enc]
        + cond_vector
        + [qty1_norm, qty2_norm, round(qty_ratio, 4), combined_norm]
    )


# ── Generate training samples ──────────────────────────────────────────────────
# Use realistic mg values in training so model sees real-world dosages
DOSE_COMBOS = [
    (500, 500), (500, 5),  (500, 1),
    (5,   500), (5,   5),  (5,   1),
    (100, 100), (100, 50), (50,  50),
    (200, 10),  (10,  10), (1,   1),
    (250, 250), (400, 200)
]

X, y = [], []

for entry in interactions:
    drug1     = entry.get("drug1", "")
    drug2     = entry.get("drug2", "")
    severity  = entry.get("severity", "low").lower()
    conditions = entry.get("conditions", [])

    if not drug1 or not drug2:
        continue

    label = SEVERITY_MAP.get(severity, 0)

    for gender in ["male", "female"]:
        for qty1, qty2 in DOSE_COMBOS:
            feats = build_features(drug1, drug2, gender, conditions, qty1, qty2)
            X.append(feats)
            y.append(label)

        # Varied conditions
        for cond_subset in [[], conditions[:1] if conditions else [], conditions]:
            feats = build_features(drug1, drug2, gender, cond_subset, 100, 100)
            X.append(feats)
            y.append(label)

X = np.array(X, dtype=float)
y = np.array(y)

print(f" Training samples: {len(X)}")
print(f"   Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
print(f"   Feature count: {X.shape[1]}")

# ── Train model ───────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
)

model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("\n Model Evaluation:")
print(classification_report(
    y_test, y_pred,
    target_names=["Low", "Moderate", "High", "Critical"],
    zero_division=0
))

# ── Save model ─────────────────────────────────────────────────────────────────
MODEL_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
META_PATH  = os.path.join(MODEL_DIR, "meta.json")

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

meta = {
    "condition_list":  CONDITION_LIST,
    "severity_map":    SEVERITY_MAP,
    "severity_labels": ["Low", "Moderate", "High", "Critical"],
    "feature_count":   X.shape[1],
    "max_dose":        MAX_DOSE,
    "max_qty_ratio":   10.0,
}
with open(META_PATH, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\nModel saved  → {MODEL_PATH}")
print(f" Metadata saved → {META_PATH}")
print("\nRun: python ml/train_model.py   (only needed once or when data changes)")
