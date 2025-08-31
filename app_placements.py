from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import re

# ---------------------------
# Initialize Flask app & Firebase
# ---------------------------
app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("serviceAccountKey.json")
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ==================================================
# Placements Logic (More Robust Version)
# ==================================================

def handle_placement_query(query: str, placement_data: list):
    """
    Finds and formats answers for placement-related questions.
    """
    query = query.lower().strip()
    
    status_doc = next((doc for doc in placement_data if "status_message" in doc), {})
    process_doc = next((doc for doc in placement_data if "steps" in doc), {})
    
    # --- Check for questions about the placement officer ---
    officer_keywords = ["officer", "coordinator", "contact", "who to contact", "person to contact", "head of placements"]
    if any(k in query for k in officer_keywords):
        officer = status_doc.get("placement_officer", {})
        name = officer.get("name")
        email = officer.get("email")
        if name and email:
            return f"The placement officer is {name}. You can contact them at: {email}."
        else:
            return "The placement officer details have not been announced yet. Please check back later."
            
    # --- Check for questions about a specific step ---
    steps = process_doc.get("steps", [])
    step_keywords = {
        "1": ["first step", "1st step", "step 1", "resume submission"],
        "2": ["second step", "2nd step", "step 2", "pre-placement talks"],
        "3": ["third step", "3rd step", "step 3", "interviews", "tests"]
    }

    for step_num, keywords in step_keywords.items():
        for keyword in keywords:
            if keyword in query:
                for step in steps:
                    if str(step.get("step") or step.get("steps")) == step_num:
                        return f"Step {step_num} is {step.get('name')}: {step.get('details')}."
                return f"I couldn't find the details for step {step_num}."

    # --- Check for questions about the overall process ---
    process_keywords = ["process", "how", "work", "procedure", "steps to apply"]
    if any(k in query for k in process_keywords):
        if steps:
            formatted_steps = []
            for step in steps:
                step_num = str(step.get("step") or step.get("steps"))
                formatted_steps.append(f"Step {step_num} is {step.get('name')}")
            return "The placement process is as follows: " + ", ".join(formatted_steps) + "."
        else:
            return "The placement process details are not available yet."

    # --- Fallback to the general status message for any other relevant keyword ---
    general_keywords = ["placement", "status", "career", "job", "opportunities", "internship", "companies", "recruiting"]
    if any(k in query for k in general_keywords):
        return status_doc.get("status_message", "Placement information is not available right now.")
        
    return "Sorry, I can only answer questions related to placements."

# ==================================================
# API ROUTE
# ==================================================
@app.route("/placements", methods=["POST"])
def placements_query():
    query = request.json.get("question", "")
    
    docs = db.collection("placementInfo").stream()
    placement_data = [doc.to_dict() for doc in docs]
    
    answer = handle_placement_query(query, placement_data)
    return jsonify({"answer": answer})

# ==================================================
if __name__ == "__main__":
    app.run(debug=True)