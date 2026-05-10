# ⬡ PharmaShield AI

**Real-time Drug Interaction Detection & Risk Analysis**

> Built with Python · Flask · scikit-learn · Groq AI (Llama 3.3) · Vanilla JS

 **Live Demo:** [pharmashield-ai.netlify.app](https://pharmashield-ai.netlify.app)
 **Backend API:** [pharmashield-ai.onrender.com](https://pharmashield-ai.onrender.com)

---

## What It Does

PharmaShield AI detects harmful drug interactions in real time. Enter any combination of medicines with dosage, gender, and medical conditions — the ML model scores the risk instantly, and Groq AI generates a plain-language explanation of what's happening and why.

**Key Features:**

-  **GradientBoosting ML model** — classifies risk as Low / Moderate / High / Critical
-  **Groq Llama 3.3** — generates personalised clinical explanations
-  **Drug pair analysis** — checks every combination of entered medicines
-  **Patient-aware** — adjusts for gender, medical conditions, and dosage
-  **Per-pair confidence breakdown** — shows probability for each risk level
-  Dark/Light theme, autocomplete, WhatsApp share, local history

---

## Project Structure

```
pharmashield-ai/
├── backend/
│   ├── data/
│   │   └── medicines.json          ← Drug name list for autocomplete
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                   ← Database connection setup
│   │   ├── models.py               ← ORM models
│   │   └── pharmashield.db         ← SQLite database (generated)
│   ├── ml/
│   │   ├── predict.py              ← Called by app.py for ML scoring
│   │   ├── train_model.py          ← Run once to train the model
│   │   ├── model.pkl               ← Generated after training
│   │   └── meta.json               ← Feature metadata (generated after training)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── check_interactions.py   ← Route handlers for /api/check
│   ├── services/
│   │   ├── __init__.py
│   │   └── ai_service.py           ← Groq AI integration
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helper.py               ← Shared utility functions
│   ├── app.py                      ← Flask server (main entry point)
│   ├── interactions.json           ← 82 drug interaction pairs (training data)
│   ├── seed.py                     ← Database seeding script
│   ├── Procfile                    ← Render deployment config
│   └── .env                        ← Groq API key (never commit this)
│
├── frontend/
│   ├── home.html                   ← Landing / home page
│   ├── index.html                  ← Main app UI
│   ├── ml_style.css                ← ML result panel styles
│   ├── script.js                   ← Frontend logic & API calls
│   └── style.css                   ← Global styles, themes
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Local Setup & Run

### Prerequisites

- Python 3.11+
- VS Code with the **Live Server** extension
- A free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Get a Groq API Key

Sign up at [console.groq.com](https://console.groq.com) (no billing required), go to **API Keys → Create API Key** and copy it.

### 2. Create the `.env` file

Inside the `backend/` folder, create a file named exactly `.env`:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

> No quotes around the key. No spaces around `=`. Windows users: make sure File Explorer shows extensions so it's not saved as `.env.txt`.

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Seed the database *(run once)*

```bash
python seed.py
```

### 5. Train the ML model *(run once)*

```bash
python ml/train_model.py
```

Expected output:
```
Training samples: 1640+
Model saved → ml/model.pkl
Metadata saved → ml/meta.json
```

### 6. Start the Flask backend

```bash
python app.py
```

Expected output:
```
 Groq AI (Llama 3) loaded successfully.
 interactions.json loaded — 82 entries.
 ML model loaded and ready.
 * Running on http://127.0.0.1:5000
```

> All three lines must appear before opening the frontend.

### 7. Open the frontend

In VS Code, right-click `frontend/index.html` → **Open with Live Server**.  
Browser opens at `http://127.0.0.1:5500`.

---

##  Deployment (Render + Netlify)

Deploy the Flask backend to Render and the static frontend to Netlify — both are free.

### Backend → Render

**Step 1:** Add a `Procfile` inside the `backend/` folder:
```
web: python app.py
```

**Step 2:** Update the last lines of `app.py` to use Render's dynamic port:
```python
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

**Step 3:** Remove `ml/model.pkl` and `ml/meta.json` from `.gitignore` and commit them, OR let Render train the model on deploy by using this build command in Render settings:
```
pip install -r ../requirements.txt && python ml/train_model.py && python seed.py
```

**Step 4:** Push to GitHub.

**Step 5:** On [render.com](https://render.com):
- New → Web Service → connect this repo
- Root Directory: `backend`
- Runtime: `Python 3`
- Build Command: `pip install -r ../requirements.txt && python ml/train_model.py && python seed.py`
- Start Command: `python app.py`
- Environment Variable: `GROQ_API_KEY = gsk_your_key`

Your backend URL will be: `https://pharmashield-ai.onrender.com`

> ⚠️ Render's free tier spins down after 15 min of inactivity. First request after sleep takes ~30s.

### Frontend → Netlify

**Step 1:** Update the API base URL in `frontend/script.js`:
```javascript
const API_BASE = "https://pharmashield-ai.onrender.com"; // your Render URL
```

**Step 2:** On [netlify.com](https://netlify.com), drag and drop the `frontend/` folder onto the deploy zone — or connect via GitHub with Base Directory set to `frontend`.

Your frontend URL will be: `https://pharmashield-ai.netlify.app`

### Fix CORS for Production

In `backend/app.py`, update CORS to allow your Netlify domain:
```python
CORS(app, origins=["https://pharmashield-ai.netlify.app"])
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves index.html |
| POST | `/api/check` | ML scoring + Groq AI explanation |
| POST | `/api/check-interactions` | Alias for `/api/check` |
| GET | `/api/medicines` | Returns all drug names for autocomplete |
| GET | `/api/model-status` | Returns `{ ml_ready: true/false }` |

### POST `/api/check` — Request Body

```json
{
  "medicines": [
    { "name": "warfarin", "dosage": "5mg" },
    { "name": "aspirin", "dosage": "100mg" }
  ],
  "gender": "female",
  "conditions": ["Diabetes", "Hypertension"],
  "patient": { "age": 65, "weight": 70 }
}
```

### POST `/api/check` — Response

```json
{
  "overall_risk": "dangerous",
  "interactions_found": 2,
  "total_pairs_checked": 1,
  "interactions": [
    {
      "drug1": "warfarin", "drug2": "aspirin",
      "severity": "dangerous",
      "effect": "Significantly increased bleeding risk...",
      "recommendation": "Avoid combination..."
    }
  ],
  "ai_explanation": "Warfarin and aspirin together...",
  "ai_source": "groq",
  "ml_result": {
    "overall_risk": "Critical",
    "confidence": 0.94,
    "ml_used": true,
    "pairs": [{ "drug1": "...", "risk_label": "Critical" }]
  }
}
```

---

## Test Combinations

| Medicines | Expected Risk | Reason |
|---|---|---|
| warfarin + aspirin | ⚠️ Critical | Additive bleeding — COX + anticoagulant |
| fluoxetine + tramadol | ⚠️ Critical | Serotonin syndrome risk |
| simvastatin + clarithromycin | ⚠️ Critical | CYP3A4 → rhabdomyolysis |
| sildenafil + nitrates | ⚠️ Critical | Fatal hypotension |
| atenolol + verapamil | ⚠️ Critical | Complete heart block risk |
| aspirin + ibuprofen | ⚡ Moderate | Competing COX-1 binding |
| metformin + furosemide | ⚡ Moderate | Lactic acidosis risk |
| paracetamol + ibuprofen | ✅ Low | Generally safe |
| cetirizine + loratadine | ✅ Low | No significant interaction |

---

## How the ML Model Works

The GradientBoosting classifier is trained on 82 curated drug pairs from `interactions.json`. Each pair is encoded into a feature vector:

- Drug name hashes (consistent numeric encoding)
- Drug pair hash (order-independent fingerprint)
- Gender encoding (male=1 / female=0)
- 10-dimensional condition vector (diabetes, hypertension, kidney disease, etc.)
- Dosage quantities and derived features (ratio, combined total)

The model outputs a risk class (0=Low, 1=Moderate, 2=High, 3=Critical) with confidence probabilities. If combined dosage exceeds 6 units, the risk is bumped up one level. If the database knows a pair is more severe than ML predicted, the database value wins.

---

## Groq AI Integration

- **Model:** `llama-3.3-70b-versatile`
- **Free tier:** 14,400 requests/day — plenty for any demo
- Groq receives the ML result and patient profile, then generates a plain-language clinical explanation
- If Groq fails, the app automatically falls back to rich text from `interactions.json` — the user always gets a response

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GROQ_API_KEY not found: False` | Check `.env` is in `backend/`, named exactly `.env`, no quotes around key |
| `Groq not configured — using fallback` | Same as above |
| `ML model not found` | Run `python ml/train_model.py` from `backend/` |
| `Could not connect to backend` | Make sure `app.py` is running on port 5000 first |
| `model_decommissioned` error | Change model name in `call_groq()` to `llama-3.3-70b-versatile` |
| CORS error in browser | Confirm `Flask-Cors` is installed and `CORS(app)` is in `app.py` |
| `interactions.json not found` | File must be in `backend/` (same level as `app.py`) |
| Render backend sleeping | Free tier spins down after 15 min — first request takes ~30s to wake |
| Netlify shows blank page | Check that `API_BASE` in `script.js` points to your Render URL, not localhost |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML + CSS + JavaScript | UI, theme, autocomplete |
| Backend | Python 3.11 + Flask | REST API, routing |
| Database | SQLite + SQLAlchemy | Drug data persistence |
| ML Model | scikit-learn GradientBoosting | Risk scoring |
| AI Explain | Groq API — Llama 3.3 70B | Clinical explanations |
| Data | interactions.json | 82 curated drug pairs |
| CORS | Flask-Cors | Frontend ↔ backend communication |
| Env | python-dotenv | Loads API key from `.env` |
| Hosting (BE) | Render | Flask backend deployment |
| Hosting (FE) | Netlify | Static frontend deployment |

---

## `.gitignore` — Never Commit These

```
.env
__pycache__/
*.pyc
database/pharmashield.db
```

> Note: `ml/model.pkl` and `ml/meta.json` should be committed if you want Render to use pre-trained weights without retraining on every deploy.

---

##  Disclaimer

PharmaShield AI is built for **educational and hackathon purposes only**. It is not a substitute for professional medical advice. Always consult a licensed healthcare provider before making any medical decision.

---

## Team

- **Chaithra P** (Backend & ML)  
  [linkedin.com/in/chaithra-p-codes](https://linkedin.com/in/chaithra-p-codes)

- **Aarathi M Iyer** (Frontend)  
  [linkedin.com/in/aarathi-iyer](https://linkedin.com/in/aarathi-iyer)

- **Abhinand J Prakash** (AI Integration)  
  [linkedin.com/in/abhinand-j-prakash](https://linkedin.com/in/abhinand-j-prakash)

---

*Shortlisted among top teams at FORGE-X 2026 Hackathon*
