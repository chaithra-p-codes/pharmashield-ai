# ⬡ PharmaShield AI

**Real-time drug interaction detection & risk analysis**

> Detects harmful drug combinations, classifies risk as Safe / Moderate / Dangerous,
> and generates AI-powered personalized safety explanations.

---

##  Project Structure

```
pharmashield-ai/
│
├── backend/
│   ├── app.py                       ← Flask server (run this)
│   ├── seed.py                      ← Run ONCE to populate DB
│   ├── database/
│   │   ├── db.py                    ← SQLAlchemy setup
│   │   ├── models.py                ← 4 DB tables
│   │   └── pharmashield.db          ← SQLite file (auto-created)
│   ├── routes/
│   │   └── check_interactions.py    ← Drug pair logic
│   ├── data/
│   │   └── medicines.json           ← Source data (40+ interactions)
│   ├── services/
│   │   └── ai_service.py            ← OpenAI + fallback
│   └── utils/
│       └── helper.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run (Step by Step)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Create your .env file
```bash
# Copy example file
cp .env.example .env

# Open .env and add your OpenAI key (optional)
# OPENAI_API_KEY=sk-your-key-here
```

### Step 3 — Seed the database (run ONCE)
```bash
cd backend
python seed.py
```

You should see:
```
Database seeded successfully!
   → 42 interactions loaded
   → 40 medicines loaded
   → 97 side effect entries loaded
   → 20 alternative entries loaded
```

### Step 4 — Start Flask backend
```bash
python app.py
```

You should see:
```
 PharmaShield AI backend starting...
 Running on http://localhost:5000
```

### Step 5 — Open frontend
- Right-click `frontend/index.html` in VS Code
- Click **"Open with Live Server"**
- Browser opens at `http://127.0.0.1:5500`

---

##  Test Combinations

| Medicines | Expected Result |
|-----------|----------------|
| warfarin + aspirin |  DANGEROUS |
| fluoxetine + tramadol |  DANGEROUS |
| metformin + alcohol | DANGEROUS |
| aspirin + ibuprofen |  MODERATE |
| ciprofloxacin + antacid |  MODERATE |
| paracetamol + ibuprofen |  SAFE |
| amoxicillin + paracetamol |  SAFE |

---

##  API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/check` | Check interactions |
| GET | `/api/medicines` | List all medicines |
| GET | `/api/sideeffects/<name>` | Side effects for a medicine |
| GET | `/api/alternatives/<name>` | Safer alternatives |

### POST `/api/check` body:
```json
{
  "medicines": ["warfarin", "aspirin"],
  "patient": {
    "age": 65,
    "weight": 70,
    "condition": "Diabetes"
  }
}
```

---

## Team Division

| Person | Role | Files |
|--------|------|-------|
| Person 1 | Frontend | `frontend/` folder |
| Person 2 | Backend + DB | `app.py`, `routes/`, `database/`, `data/` |
| Person 3 | AI + Integration | `services/ai_service.py`, `.env`, testing |

---

## Tech Stack

- **Frontend:** HTML + CSS + JavaScript
- **Backend:** Python + Flask + Flask-CORS
- **Database:** SQLite via Flask-SQLAlchemy (4 tables)
- **AI:** OpenAI GPT-3.5-turbo (with built-in fallback)
- **Data:** 40+ drug interaction pairs, side effects, alternatives

---

## Disclaimer

For educational and hackathon purposes only.
Always consult a licensed healthcare provider for medical decisions.
