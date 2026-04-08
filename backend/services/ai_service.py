import os
from openai import OpenAI


def generate_ai_explanation(medicines, interactions, overall_risk, patient={}):
    """
    Generate a human-friendly AI explanation.
    Personalizes output using patient age, weight, condition if provided.
    Only calls OpenAI for moderate/dangerous — uses fallback for safe.
    """

    # For safe results skip OpenAI to save tokens
    if overall_risk in ["safe", "no_interactions_found"]:
        return generate_fallback_explanation(interactions, overall_risk)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "dummy":
        return generate_fallback_explanation(interactions, overall_risk, patient)

    try:
        client = OpenAI(api_key=api_key)

        # Build interaction summary
        interaction_text = ""
        for i in interactions:
            interaction_text += f"- {i['drug1']} + {i['drug2']} → {i['severity'].upper()}: {i['effect']}\n"

        # Build patient context
        patient_context = ""
        age       = patient.get('age', '')
        weight    = patient.get('weight', '')
        condition = patient.get('condition', '')

        if age:
            patient_context += f"The patient is {age} years old. "
        if weight:
            patient_context += f"They weigh {weight} kg. "
        if condition and condition != 'None':
            patient_context += f"They have a pre-existing condition: {condition}. "

        prompt = f"""You are PharmaShield AI, a caring medical safety assistant.

{patient_context}
The patient is currently taking: {', '.join(medicines)}.

Drug interactions detected:
{interaction_text}
Overall risk level: {overall_risk.upper()}

In 3-4 clear sentences:
1. Explain the most important risk in simple language
2. Give one specific action the patient should take
3. Reassure them to consult their doctor

Be compassionate and avoid overly technical terms. Write in natural paragraph form, no bullet points."""

        response = client.chat.completions.create(
            model      = "gpt-3.5-turbo",
            messages   = [
                {"role": "system", "content": "You are a helpful, caring medical safety assistant. Keep explanations clear and actionable for non-medical users."},
                {"role": "user",   "content": prompt}
            ],
            max_tokens  = 220,
            temperature = 0.7
        )

        return {
            "source":      "openai",
            "explanation": response.choices[0].message.content.strip()
        }

    except Exception as e:
        print(f"⚠️ OpenAI error: {e} — using fallback")
        return generate_fallback_explanation(interactions, overall_risk, patient)


def generate_fallback_explanation(interactions, overall_risk, patient={}):
    """Built-in explanation when OpenAI is unavailable."""

    age       = patient.get('age', '')
    condition = patient.get('condition', '')

    patient_note = ""
    if age or (condition and condition != 'None'):
        parts = []
        if age:       parts.append(f"{age} years old")
        if condition and condition != 'None': parts.append(f"with {condition}")
        patient_note = f" For a patient {' '.join(parts)}, extra caution is advised."

    if overall_risk == "dangerous":
        dangerous = [i for i in interactions if i["severity"] == "dangerous"]
        top = dangerous[0] if dangerous else interactions[0]
        msg = (
            f"A dangerous interaction was detected between {top['drug1']} and {top['drug2']}. "
            f"{top['effect']}{patient_note} "
            f"{top['recommendation']} "
            f"Please consult your doctor or pharmacist immediately before continuing this combination."
        )

    elif overall_risk == "moderate":
        moderate = [i for i in interactions if i["severity"] == "moderate"]
        top = moderate[0] if moderate else interactions[0]
        msg = (
            f"A moderate interaction was detected between {top['drug1']} and {top['drug2']}. "
            f"{top['effect']}{patient_note} "
            f"{top['recommendation']} "
            f"We recommend discussing this with your healthcare provider at your next visit."
        )

    elif overall_risk in ["safe", "no_interactions_found"]:
        msg = (
            "The medicines you entered appear to be safe to take together based on our database. "
            "No harmful interactions were found. "
            "However, always follow your doctor's guidance and report any unusual symptoms."
        )

    else:
        msg = "Unable to determine interaction status. Please consult your pharmacist."

    return {
        "source":      "fallback",
        "explanation": msg
    }
