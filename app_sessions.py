from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

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
# Sessions Logic (Final Corrected Version)
# ==================================================

# --- More robust keyword map with conversational names ---
SESSION_KEYWORDS = {
    "Seminar on Cybersecurity and Safety": ["cybersecurity", "safety", "rajesh mahadik", "rajesh sir"],
    "Bridge Course: Statistics using Excel": ["statistics", "excel", "bridge course", "rahul yadav", "rahul sir"],
    "Session on Cloud Computing": ["cloud computing", "cloud", "abhishek maurya", "abhishek sir"],
    "Ace Your Space: Resume & Job Skills": ["resume", "job skills", "placement training", "darpana more", "darpana mam"]
}

def format_session_details(session: dict) -> str:
    """Creates a clean, readable summary of a specific session."""
    title = session.get('title', 'N/A')
    category = session.get('category', 'Session')
    speaker = session.get('speaker') or session.get('facilitator', 'N/A')
    date = session.get('date', 'N/A')
    time = session.get('time', 'N/A')
    venue = session.get('venue', 'N/A')
    
    summary = f"The '{title}' ({category}) was held on {date} at {time} in {venue}. It was conducted by {speaker}."
    
    topics = session.get('topics_covered', [])
    if topics:
        summary += " Topics covered included: " + ", ".join(topics) + "."
        
    return summary

def handle_sessions_query(query: str, sessions_data: list):
    """
    Finds and formats answers for questions about past sessions.
    """
    query = query.lower().strip()
    
    # --- Step 1: Use the new keyword map to find a specific session ---
    target_session_title = None
    for session_title, keywords in SESSION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query:
                target_session_title = session_title
                break
        if target_session_title:
            break

    # If we found a direct match, return its details
    if target_session_title:
        for session in sessions_data:
            if session.get('title') == target_session_title:
                return format_session_details(session)
        return f"I found a match for '{target_session_title}' but couldn't retrieve its details."

    # --- Step 2: Handle temporal questions ---
    if "recent" in query or "last" in query:
        latest_session = None
        latest_date = datetime.min
        for session in sessions_data:
            try:
                date_str = session.get('date', '').split(' to ')[0]
                session_date = datetime.strptime(date_str, "%Y-%m-%d")
                if session_date > latest_date:
                    latest_date = session_date
                    latest_session = session
            except ValueError:
                continue
        if latest_session:
            return "The most recent session was: " + format_session_details(latest_session)

    # --- Step 3: If no specific match, provide a general summary ---
    if sessions_data:
        summary = "We have information on the following sessions: " + ", ".join([s.get('title', 'Untitled') for s in sessions_data])
        return summary + ". Which of these sessions would you like to know more about?"

    return "Sorry, I couldn't find any information on past sessions."

# ==================================================
# API ROUTE
# ==================================================
@app.route("/sessions", methods=["POST"])
def sessions_query():
    query = request.json.get("question", "")
    
    docs = db.collection("sessions").stream()
    sessions_data = [doc.to_dict() for doc in docs]
    
    answer = handle_sessions_query(query, sessions_data)
    return jsonify({"answer": answer})

# ==================================================
if __name__ == "__main__":
    app.run(debug=True)