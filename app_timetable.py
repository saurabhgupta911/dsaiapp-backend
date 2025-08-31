from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import re
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
# Timetables Logic (Final Conversational Version)
# ==================================================

SEMESTER_MAP = {
    "First Year - Semester 1": ["first year", "fy", "sem 1", "semester 1"],
    "Second Year - Semester 3": ["second year", "sy", "sem 3", "semester 3"],
    "Third Year - Semester 5": ["third year", "ty", "sem 5", "semester 5"]
}
PROFESSOR_NAMES = ["rahul", "sujata", "mujtaba", "wasif", "darpana", "akash", "shweta", "deepak"]


def format_day_schedule(day: str, schedule: dict) -> str:
    """Creates a clean, readable summary of a single day's schedule."""
    if not schedule.get('lectures') or (isinstance(schedule['lectures'], list) and len(schedule['lectures']) > 0 and not schedule['lectures'][0]):
        return f"There are no lectures scheduled for {day}."

    summary = f"On {day}, the schedule is: "
    lecture_details = []
    lectures = schedule.get('lectures') or schedule.get('lecture', [])
    for lecture in lectures:
        if isinstance(lecture, dict):
            subject = lecture.get('subject', 'N/A')
            time = lecture.get('time', 'N/A')
            prof = lecture.get('professor', 'N/A')
            lecture_details.append(f"{subject} with Prof. {prof} from {time}")

    summary += ", ".join(lecture_details) + f" in classroom {schedule.get('classroom') or schedule.get('Classroom', 'N/A')}."
    return summary

def handle_timetable_query(query: str, timetables_data: list, state: str = None, original_query: str = None):
    """
    Finds and formats answers for timetable-related questions using conversational state.
    """
    query = query.lower().strip()

    # --- Step 1: Handle the follow-up response from the user ---
    if state == "AWAITING_YEAR_CLARIFICATION":
        # The user has replied with a year. Combine it with their original question.
        full_query = f"{original_query} for {query}"
        # Now, re-run the logic with the complete question, but without a state
        return handle_timetable_query(full_query, timetables_data)

    # --- Step 2: Normal logic for a new question ---
    target_semester_name = None
    for sem_name, keywords in SEMESTER_MAP.items():
        for keyword in keywords:
            if keyword in query:
                target_semester_name = sem_name
                break
        if target_semester_name:
            break

    # --- Step 3: Handle professor-specific questions ---
    target_prof = None
    for prof in PROFESSOR_NAMES:
        if prof in query:
            target_prof = prof
            break
    
    if target_prof:
        # If the year is also mentioned, we can be specific
        if target_semester_name:
            target_timetable = next((tt for tt in timetables_data if tt.get('semester_name') == target_semester_name), {})
            prof_schedule = []
            for day, day_schedule in target_timetable.get("schedule", {}).items():
                lectures = day_schedule.get("lectures") or day_schedule.get("lecture", [])
                for lecture in lectures:
                    if isinstance(lecture, dict) and lecture.get("professor", "").lower() == target_prof:
                        prof_schedule.append(f"on {day}: {lecture.get('subject')} at {lecture.get('time')}")
            if prof_schedule:
                return f"For {target_semester_name}, Prof. {target_prof.title()}'s schedule is: " + ", ".join(prof_schedule) + "."
            else:
                return f"Prof. {target_prof.title()} has no lectures for {target_semester_name}."
        else:
            # If no year is mentioned, ask for clarification
            return {
                "answer": f"I can get the schedule for Prof. {target_prof.title()}. Which year are you asking about?",
                "new_state": "AWAITING_YEAR_CLARIFICATION",
                "original_question": query
            }

    # --- Step 4: Handle general timetable questions with a specified year ---
    if target_semester_name:
        target_timetable = next((tt for tt in timetables_data if tt.get('semester_name') == target_semester_name), None)
        if not target_timetable: return f"I'm sorry, I couldn't find timetable data for {target_semester_name}."
        
        schedule = target_timetable.get('schedule', {})
        # ... (Your "today" and "next lecture" logic would go here)
        
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days_of_week:
            if day in query:
                day_schedule = schedule.get(day.title())
                if day_schedule and day_schedule.get('lectures') and day_schedule['lectures'][0]:
                    return format_day_schedule(day.title(), day_schedule)
                else:
                    return f"There are no lectures scheduled for {day.title()} for {target_semester_name}."
        
        full_summary = f"Here is the full weekly schedule for {target_semester_name}: "
        for day, day_schedule in schedule.items():
            full_summary += format_day_schedule(day, day_schedule) + " "
        return full_summary.strip()
        
    # --- Step 5: If no year OR professor is mentioned, ask for clarification ---
    return {
        "answer": "I can help with the timetable. Please specify a year or a professor's name.",
        "new_state": "AWAITING_YEAR_CLARIFICATION",
        "original_question": query
    }

# ==================================================
# API ROUTE
# ==================================================
@app.route("/timetable", methods=["POST"])
def timetable_query():
    data = request.json
    query = data.get("question", "")
    state = data.get("conversation_state")
    original_query = data.get("original_question")
    
    docs = db.collection("timetables").stream()
    timetables_data = [doc.to_dict() for doc in docs]
    
    response_data = handle_timetable_query(query, timetables_data, state, original_query)

    # If the handler returns a dictionary (because it's asking a question), return it as is
    if isinstance(response_data, dict):
        return jsonify(response_data)
    
    # Otherwise, it's a final answer string
    return jsonify({"answer": response_data, "new_state": "DEFAULT"})

# ==================================================
if __name__ == "__main__":
    app.run(debug=True)