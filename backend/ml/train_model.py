"""
PharmaShield AI - ML Model Training Script
Run this once: python ml/train_model.py
It reads interactions.json and trains a risk classifier.
"""

import json
import pickle
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from itertools import combinations

# ── Load your existing interactions.json ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR,"..","..","interactions.json")
DATA_PATH=os.path.abspath(DATA_PATH)
print("DEBUG PATH:", DATA_PATH)

with open(DATA_PATH, "r") as f:
    raw_data = json.load(f)

# ── Expected JSON structure (adapt if yours differs) ──────────────────────────
# {
#   "interactions": [
#     {
#       "drug1": "Warfarin", "drug2": "Aspirin",
#       "severity": "High",          <- Low / Moderate / High / Critical
#       "conditions": ["bleeding"],   <- conditions that worsen it
#       "mechanism": "..."
#     }, ...
#   ]
# }
#
# If your JSON has a different shape, adjust the parsing below.

interactions = raw_data.get("interactions", raw_data)  # handle both shapes

# ── Build training samples ─────────────────────────────────────────────────────
SEVERITY_MAP = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
CONDITION_LIST = [
    "diabetes", "hypertension", "kidney_disease", "liver_disease",
    "heart_disease", "asthma", "bleeding_disorder", "pregnancy",
    "elderly", "renal_impairment"
]

def build_features(drug1, drug2, gender, conditions, qty1, qty2):
    """
    Returns a flat feature vector:
    [drug1_hash, drug2_hash, gender_enc, *conditions_onehot, qty1_norm, qty2_norm,
     qty_ratio, combined_qty]
    """
    # Simple hash-based encoding for drug names (consistent but not learned)
    d1 = abs(hash(drug1.lower().strip())) % 10000
    d2 = abs(hash(drug2.lower().strip())) % 10000
    drug_pair_hash = abs(hash(tuple(sorted([drug1.lower(), drug2.lower()])))) % 10000

    gender_enc = 1 if str(gender).lower() in ["male", "m"] else 0

    cond_vector = [1 if c in [x.lower().replace(" ", "_") for x in conditions] else 0
                   for c in CONDITION_LIST]

    qty1 = float(qty1) if qty1 else 1.0
    qty2 = float(qty2) if qty2 else 1.0
    qty_ratio = qty1 / (qty2 + 1e-6)
    combined_qty = qty1 + qty2

    return [d1, d2, drug_pair_hash, gender_enc] + cond_vector + [
        qty1, qty2, round(qty_ratio, 4), combined_qty
    ]

# ── Generate training data from interactions.json ─────────────────────────────
X, y = [], []

for entry in interactions:
    drug1 = entry.get("drug1", "")
    drug2 = entry.get("drug2", "")
    severity = entry.get("severity", "low").lower()
    conditions = entry.get("conditions", [])

    if not drug1 or not drug2:
        continue

    label = SEVERITY_MAP.get(severity, 0)

    # Generate multiple samples per pair with varied inputs to help generalization
    for gender in ["male", "female"]:
        for qty_combo in [(1, 1), (2, 1), (1, 2), (3, 2)]:
            feats = build_features(drug1, drug2, gender, conditions, qty_combo[0], qty_combo[1])
            X.append(feats)
            y.append(label)

        # Sample with common conditions
        for cond_subset in [[], conditions[:1] if conditions else [], conditions]:
            feats = build_features(drug1, drug2, gender, cond_subset, 1, 1)
            X.append(feats)
            y.append(label)

X = np.array(X, dtype=float)
y = np.array(y)

print(f"✅ Training samples: {len(X)}")
print(f"   Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

# ── Train model ───────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("\n📊 Model Evaluation:")
print(classification_report(y_test, y_pred,
      target_names=["Low", "Moderate", "High", "Critical"],
      zero_division=0))

# ── Save model ────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
META_PATH = os.path.join(MODEL_DIR, "meta.json")

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

# Save metadata (feature names, condition list, severity map)
meta = {
    "condition_list": CONDITION_LIST,
    "severity_map": SEVERITY_MAP,
    "severity_labels": ["Low", "Moderate", "High", "Critical"],
    "feature_count": X.shape[1]
}
with open(META_PATH, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\n✅ Model saved → {MODEL_PATH}")
print(f"✅ Metadata saved → {META_PATH}")
print("\nRun: python ml/train_model.py   (only needed once or when data changes)")
