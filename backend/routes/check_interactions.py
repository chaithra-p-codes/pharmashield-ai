from itertools import combinations


def normalize_name(name):
    return name.strip().lower()


def get_severity_order(severity):
    return {"safe": 0, "moderate": 1, "dangerous": 2}.get(severity, 0)


def check_drug_interactions(medicine_list):
    """
    Check all pairwise interactions for a list of medicines using SQLite DB.
    Returns interactions sorted by severity (dangerous first).
    """
    from database.models import Interaction

    normalized_input = [normalize_name(m) for m in medicine_list if m.strip()]

    if len(normalized_input) < 2:
        return {
            "status":       "insufficient",
            "message":      "Please enter at least 2 medicines to check interactions.",
            "interactions": [],
            "overall_risk": "unknown"
        }

    found_interactions = []

    for med1, med2 in combinations(normalized_input, 2):
        # Check both orders in DB
        interaction = (
            Interaction.query.filter_by(drug1=med1, drug2=med2).first() or
            Interaction.query.filter_by(drug1=med2, drug2=med1).first()
        )
        if interaction:
            found_interactions.append(interaction.to_dict())

    # Sort: dangerous → moderate → safe
    found_interactions.sort(
        key=lambda x: get_severity_order(x["severity"]),
        reverse=True
    )

    # Overall risk = worst case found
    if any(i["severity"] == "dangerous" for i in found_interactions):
        overall_risk = "dangerous"
    elif any(i["severity"] == "moderate" for i in found_interactions):
        overall_risk = "moderate"
    elif found_interactions:
        overall_risk = "safe"
    else:
        overall_risk = "no_interactions_found"

    return {
        "status":              "ok",
        "medicines_checked":   normalized_input,
        "interactions":        found_interactions,
        "overall_risk":        overall_risk,
        "total_pairs_checked": len(list(combinations(normalized_input, 2))),
        "interactions_found":  len(found_interactions)
    }
