from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__)
    CORS(app)

    # ── SQLite config ──────────────────────────────────
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'database', 'pharmashield.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Initialize DB ──────────────────────────────────
    from database.db import init_db
    init_db(app)

    # ── Routes ─────────────────────────────────────────

    @app.route('/', methods=['GET'])
    def health_check():
        return jsonify({"status": "PharmaShield AI backend is running ✅"})


    @app.route('/api/check', methods=['POST'])
    def check_medicines():
        """
        Main endpoint — receives medicines list + optional patient info.
        Returns interactions + AI explanation.

        Request body:
        {
            "medicines": ["warfarin", "aspirin"],
            "patient": { "age": 65, "weight": 70, "condition": "Diabetes" }
        }
        """
        try:
            data = request.get_json()

            if not data or 'medicines' not in data:
                return jsonify({"error": "Please provide a medicines list."}), 400

            medicines = data['medicines']
            patient   = data.get('patient', {})

            if not isinstance(medicines, list) or len(medicines) == 0:
                return jsonify({"error": "medicines must be a non-empty list."}), 400

            # Step 1: check interactions from DB
            from routes.check_interactions import check_drug_interactions
            result = check_drug_interactions(medicines)

            # Step 2: generate AI explanation
            if result["status"] == "ok":
                from services.ai_service import generate_ai_explanation
                ai_response = generate_ai_explanation(
                    medicines    = result["medicines_checked"],
                    interactions = result["interactions"],
                    overall_risk = result["overall_risk"],
                    patient      = patient
                )
                result["ai_explanation"] = ai_response["explanation"]
                result["ai_source"]      = ai_response["source"]

            return jsonify(result), 200

        except Exception as e:
            print(f"❌ Error in /api/check: {e}")
            return jsonify({"error": "Internal server error. Please try again."}), 500


    @app.route('/api/medicines', methods=['GET'])
    def get_medicines_list():
        """Return all known medicine names for autocomplete."""
        try:
            from database.models import Medicine
            medicines = Medicine.query.order_by(Medicine.name).all()
            return jsonify({"medicines": [m.name for m in medicines]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route('/api/sideeffects/<medicine>', methods=['GET'])
    def get_side_effects(medicine):
        """Return side effects for a specific medicine."""
        try:
            from database.models import SideEffect
            effects = SideEffect.query.filter_by(medicine=medicine.lower()).all()
            return jsonify({
                "medicine":     medicine.lower(),
                "side_effects": [e.effect for e in effects]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route('/api/alternatives/<medicine>', methods=['GET'])
    def get_alternatives(medicine):
        """Return safer alternative medicines."""
        try:
            from database.models import Alternative
            alts = Alternative.query.filter_by(medicine=medicine.lower()).all()
            return jsonify({
                "medicine":     medicine.lower(),
                "alternatives": [a.alternative for a in alts]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    return app


if __name__ == '__main__':
    app = create_app()
    print("🚀 PharmaShield AI backend starting...")
    print("📡 Running on http://localhost:5000")
    app.run(debug=True, port=5000)
