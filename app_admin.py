from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------------------
# Initialize Flask app & Firebase
# ---------------------------
app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ==================================================
# Admin Info Logic
# ==================================================

# This map connects user keywords to the exact data field in your Firestore.
KEYWORD_MAP = {
    "office_hours": ["office hours", "office timing", "office open", "office close"],
    "library_hours": ["library hours", "library timing", "library open", "library close"],
    "canteen_hours": ["canteen hours", "canteen timing", "canteen open", "canteen close"],
    "principal_name": ["principal", "principal's name", "head"], # <-- "head" added here
    "general_email": ["email", "college email", "email address"],
    "address": ["address", "location", "where is the college", "where"], # <-- "where" added here
    "landline_1": ["phone", "contact", "landline", "college number"],
    "librarian_name": ["librarian", "librarian's name"],
    "attendance_policy": ["attendance", "attendance policy", "attendance rule"],
    "id_card_policy": ["id card", "identity card", "id policy"],
    "anti_ragging_helpline": ["ragging", "anti-ragging", "helpline"]
}

def handle_admin_info(query: str, admin_data: list):
    """
    Finds and formats answers for admin, contact, and policy questions.
    """
    query = query.lower().strip()

    # --- Check for specific questions first ---
    for field, keywords in KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in query:
                # Find the data point in any of the documents
                for doc in admin_data:
                    if field in doc:
                        return f"The {keyword.replace('_', ' ')} is: {doc[field]}."
                return "I couldn't find that specific information."

    # --- Check for general category questions ---
    if "timing" in query or "hours" in query:
        for doc in admin_data:
            if doc.get("category") == "College Timings":
                answer = (f"Here are the college timings: "
                          f"* Office Hours: {doc['office_hours']} "
                          f"* Library Hours: {doc['library_hours']} "
                          f"* Canteen Hours: {doc['canteen_hours']}")
                return answer

    if "contact" in query or "address" in query:
        for doc in admin_data:
            if doc.get("category") == "Contact Information":
                 answer = (f"Here is the contact information: "
                           f"* Principal: {doc['principal_name']} "
                           f"* Address: {doc['address']} "
                           f"* General Email: {doc['general_email']} "
                           f"* Phone: {doc['landline_1']}")
                 return answer

    if "policy" in query or "policies" in query or "rule" in query:
        for doc in admin_data:
            if doc.get("category") == "College Policies":
                answer = (f"Here are the key college policies: "
                          f"* Attendance: {doc['attendance_policy']} "
                          f"* ID Card: {doc['id_card_policy']} "
                          f"* Anti-Ragging Helpline: {doc['anti_ragging_helpline']}")
                return answer

    return "Sorry, I can't answer that. I can help with college timings, contact information, and policies."

# ==================================================
# API ROUTE
# ==================================================
@app.route("/admin", methods=["POST"])
def admin_query():
    query = request.json.get("question", "")
    
    docs = db.collection("adminInfo").stream()
    admin_data = [doc.to_dict() for doc in docs]
    
    answer = handle_admin_info(query, admin_data)
    return jsonify({"answer": answer})

# ==================================================
if __name__ == "__main__":
    app.run(debug=True)