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
# Co-Curricular Activities Logic (Final Corrected Version)
# ==================================================

ACTIVITY_KEYWORDS = {
    "Rotaract Club of Ramniranjan Jhunjhunwala College": ["rotaract", "rcrj"],
    "NSS (National Service Scheme)": ["nss", "national service scheme"],
    "NCC (National Cadet Corps)": ["ncc", "national cadet corps"],
    "DLLE (Lifelong Learning and Extension)": ["dlle", "lifelong learning"]
}

def get_specific_detail(query: str, activity: dict) -> str:
    """Checks for specific keywords and returns the requested detail."""
    
    # Using re.search with word boundaries (\b) for a precise match
    
    if re.search(r'\b(contact|person|who to contact)\b', query):
        contact = activity.get('contact_person', {})
        if contact and any(contact.values()):
            return "Here is the contact information: " + ", ".join([f"{k.title()}: {v}" for k, v in contact.items() if v])
        return f"No specific contact person is listed for {activity.get('name')}."

    if re.search(r'\b(fee|fees|cost|price)\b', query):
        if 'registration_fee' in activity:
            return f"The registration fee for {activity.get('name')} is {activity['registration_fee']}."
        if 'registration_fees' in activity:
            fees_data = activity['registration_fees']
            if '2024-2025' in fees_data:
                year_fees = fees_data['2024-2025']
                return f"The registration fees for {activity.get('name')} for 2024-2025 are: Year 1 - {year_fees.get('1', 'N/A')}, Year 2 - {year_fees.get('2', 'N/A')}."
            if 'status' in fees_data:
                return f"There is {fees_data['status']} for {activity.get('name')}."
        return f"I could not find specific fee information for {activity.get('name')}."
    
    if re.search(r'\b(enroll|enrollment|join|process)\b', query):
        process = activity.get('enrollment_process', [])
        if process:
            steps = [f"Step {item['step']}: {item['name']} - {item['details']}" for item in process]
            return f"The enrollment process for {activity.get('name')} is as follows: " + " ".join(steps)
        return f"No specific enrollment process is listed for {activity.get('name')}."
        
    if re.search(r'\b(benefit|benefits)\b', query):
        benefits = activity.get('benefits', [])
        if benefits:
            return f"The benefits of joining {activity.get('name')} are: " + ", ".join(benefits) + "."
        return f"No specific benefits are listed for {activity.get('name')}."

    return None

def format_full_summary(activity: dict) -> str:
    """Creates a comprehensive summary of a club."""
    name = activity.get('name', 'N/A')
    description = activity.get('description', 'No description available.')
    benefits_list = activity.get('benefits', [])
    benefits_str = ""
    if benefits_list:
        benefits_str = "Benefits include: " + ", ".join(benefits_list) + "."
    
    return f"{name}: {description} {benefits_str}"


def handle_cocurricular_query(query: str, activities_data: list):
    """
    Finds and formats answers for co-curricular activity questions.
    """
    query = query.lower().strip()

    target_activity_name = None
    for activity_name, keywords in ACTIVITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query:
                target_activity_name = activity_name
                break
        if target_activity_name:
            break

    if target_activity_name:
        for activity in activities_data:
            if activity.get('name') == target_activity_name:
                specific_detail = get_specific_detail(query, activity)
                if specific_detail:
                    return specific_detail
                return format_full_summary(activity)
        return f"I couldn't find the details for {target_activity_name}."

    if "compulsory" in query or "mandatory" in query:
        compulsory_activities = []
        year_str = "1"
        if "second" in query or "sy" in query: year_str = "2"
        if "third" in query or "ty" in query: year_str = "3"

        for activity in activities_data:
            status = activity.get("enrollment_status", {}).get(year_str, "Optional").lower()
            if status == "compulsory":
                compulsory_activities.append(activity.get('name'))
        if compulsory_activities:
            return f"The compulsory activities are: {', '.join(compulsory_activities)}."

    summary = "We have several co-curricular activities available: " + ", ".join([act.get('name', '') for act in activities_data])
    summary += ". Which one would you like to know more about?"
    return summary

# ==================================================
# API ROUTE
# ==================================================
@app.route("/cocurricular", methods=["POST"])
def cocurricular_query():
    query = request.json.get("question", "")
    docs = db.collection("coCurricularActivities").stream()
    activities_data = [doc.to_dict() for doc in docs]
    answer = handle_cocurricular_query(query, activities_data)
    clean_answer = answer.replace('\n', ' ').replace('  ', ' ')
    return jsonify({"answer": clean_answer})

# ==================================================
if __name__ == "__main__":
    app.run(debug=True)