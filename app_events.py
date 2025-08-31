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
# Events Logic (Final Corrected Version)
# ==================================================

EVENT_KEYWORDS = {
    "Inter-Collegiate Departmental Festival 'INCEPTION' 2024": ["2024", "last year"],
    "Inter-Collegiate Departmental Festival 'INCEPTION 2.0'": ["2025", "inception 2.0", "most recent"],
    "Inter-Collegiate Departmental Festival 'INCEPTION' 2026": ["2026", "next", "upcoming", "future", "planned"]
}

def format_schedule(event: dict) -> str:
    """Creates a clean, readable summary of an event's schedule."""
    name = event.get('name', 'the event')
    schedule_data = event.get('schedule', [])
    
    if not schedule_data or not schedule_data[0]:
        return f"The schedule for {name} has not been announced yet."

    full_schedule_str = f"Here is the schedule for {name}: "
    
    for day_info in schedule_data:
        # --- THIS IS THE BUG FIX ---
        # Add a check to ensure day_info is a dictionary before processing
        if not isinstance(day_info, dict):
            continue

        day = day_info.get('day', 'N/A')
        full_schedule_str += f"On {day}, the activities were: "
        activities = day_info.get('activities', [])
        
        if activities and isinstance(activities[0], str):
            full_schedule_str += ", ".join(activities) + ". "
        elif activities and isinstance(activities[0], dict):
            activity_details = []
            for act in activities:
                act_name = act.get('name', 'N/A')
                act_time = act.get('time', 'N/A')
                activity_details.append(f"{act_name} at {act_time}")
            full_schedule_str += ", ".join(activity_details) + ". "
            
    return full_schedule_str.strip()

def count_activities(event: dict) -> int:
    """Counts the number of activities in an event's schedule."""
    count = 0
    for day in event.get('schedule', []):
        if isinstance(day, dict):
            count += len(day.get('activities', []))
    return count

def handle_events_query(query: str, events_data: list):
    """
    Finds and formats answers for questions about college events.
    """
    query = query.lower().strip()

    # --- Step 1: Handle Comparative Questions ---
    if "more activities" in query and "2024" in query and "2025" in query:
        event_2024 = next((e for e in events_data if e['name'] == "Inter-Collegiate Departmental Festival 'INCEPTION' 2024"), None)
        event_2025 = next((e for e in events_data if e['name'] == "Inter-Collegiate Departmental Festival 'INCEPTION 2.0'"), None)
        
        if event_2024 and event_2025:
            count_2024 = count_activities(event_2024)
            count_2025 = count_activities(event_2025)
            if count_2025 > count_2024:
                return f"Inception 2025 had more activities ({count_2025}) compared to Inception 2024 ({count_2024})."
            else:
                return f"Inception 2024 had more or equal activities ({count_2024}) compared to Inception 2025 ({count_2025})."

    # --- Step 2: Identify the primary event the user is asking about ---
    target_event = None
    for event_name, keywords in EVENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query:
                target_event = next((e for e in events_data if e.get('name') == event_name), None)
                break
        if target_event:
            break
    
    # --- Step 3: If a specific event is found, provide details for it ---
    if target_event:
        # Check for activity-specific questions first
        for day in target_event.get('schedule', []):
            if isinstance(day, dict):
                for activity in day.get('activities', []):
                    activity_name = ""
                    # Handle both string and dict activity formats
                    if isinstance(activity, dict):
                        activity_name = activity.get('name', '').lower()
                    elif isinstance(activity, str):
                        activity_name = re.sub(r'\(.*\)', '', activity).strip().lower()

                    if activity_name and activity_name in query:
                        if "day" in query:
                            return f"The activity '{activity_name}' at {target_event.get('name')} was on {day.get('day')}."
                        if "venue" in query:
                            venue = activity.get('venue', 'not specified') if isinstance(activity, dict) else target_event.get('venue', 'not specified')
                            return f"The venue for '{activity_name}' was {venue}."
                        # Default to providing all details for the specific activity
                        details = []
                        if isinstance(activity, dict):
                            if activity.get('time'): details.append(f"Time: {activity.get('time')}")
                            if activity.get('fee'): details.append(f"Fee: {activity.get('fee')}")
                            if activity.get('venue'): details.append(f"Venue: {activity.get('venue')}")
                        if not details:
                            return f"No specific details like time or fee are listed for '{activity_name}'."
                        return f"For the activity '{activity_name}': " + ", ".join(details)

        # If not asking about a specific activity, check for general details
        if "schedule" in query or "list all" in query or "activities" in query:
            return format_schedule(target_event)
        if "date" in query or "when" in query:
            return f"The dates for {target_event['name']} were {target_event.get('date_summary', 'To be announced')}."
        
        # Default to a general summary
        return (f"{target_event['name']} ({target_event.get('status', 'N/A')}): "
                f"{target_event.get('description') or target_event.get('report_summary', 'No summary available.')}")

    # --- Step 4: Handle "Not Found" cases ---
    if "2023" in query:
        return "I'm sorry, I don't have any information for events from 2023."

    # --- Step 5: If no specific event is identified, provide a general list ---
    summary = "We have information on the following fests: " + ", ".join([event.get('name') for event in events_data])
    return summary + ". Which one would you like to know more about?"

# ==================================================
# API ROUTE
# ==================================================
@app.route("/events", methods=["POST"])
def events_query():
    query = request.json.get("question", "")
    
    docs = db.collection("events").stream()
    events_data = [doc.to_dict() for doc in docs]
    
    answer = handle_events_query(query, events_data)
    if answer is None:
        answer = "Sorry, I couldn't find an answer for that."
        
    clean_answer = answer.replace('\n', ' ').replace('  ', ' ')
    return jsonify({"answer": clean_answer})

# ==================================================
if __name__ == "__main__":
    app.run(debug=True)