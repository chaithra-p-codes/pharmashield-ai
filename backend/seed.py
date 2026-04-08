"""
Run this ONCE to populate the SQLite database from medicines.json.

Usage:
    cd backend
    python seed.py
"""

import json
import os
import sys

# Make sure imports work from backend folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def seed_database():
    from app import create_app
    from database.db import db
    from database.models import Interaction, Medicine, SideEffect, Alternative

    app = create_app()

    with app.app_context():
        # Clear existing data and recreate tables
        db.drop_all()
        db.create_all()
        print("🗃️  Tables created fresh")

        # Load JSON source file
        json_path = os.path.join(os.path.dirname(__file__), 'data', 'medicines.json')
        with open(json_path, 'r') as f:
            data = json.load(f)

        # ── Seed interactions ──────────────────────────
        for item in data.get('interactions', []):
            db.session.add(Interaction(
                drug1          = item['drug1'],
                drug2          = item['drug2'],
                severity       = item['severity'],
                effect         = item['effect'],
                recommendation = item['recommendation']
            ))

        # ── Seed medicines list ────────────────────────
        for name in data.get('medicines_list', []):
            db.session.add(Medicine(name=name))

        # ── Seed side effects ──────────────────────────
        for medicine, effects in data.get('side_effects', {}).items():
            for effect in effects:
                db.session.add(SideEffect(medicine=medicine, effect=effect))

        # ── Seed alternatives ──────────────────────────
        for medicine, alts in data.get('alternatives', {}).items():
            for alt in alts:
                db.session.add(Alternative(medicine=medicine, alternative=alt))

        db.session.commit()

        print("✅ Database seeded successfully!")
        print(f"   → {Interaction.query.count()} interactions loaded")
        print(f"   → {Medicine.query.count()} medicines loaded")
        print(f"   → {SideEffect.query.count()} side effect entries loaded")
        print(f"   → {Alternative.query.count()} alternative entries loaded")
        print("\n🚀 You can now run: python app.py")


if __name__ == '__main__':
    seed_database()
