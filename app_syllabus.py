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
# Courses & Syllabus Logic (Final Corrected Version)
# ==================================================

SEMESTER_MAP = {
    "sem1": ["first year", "fy", "sem 1", "semester 1"],
    "sem3": ["second year", "sy", "sem 3", "semester 3"],
    "sem5": ["third year", "ty", "sem 5", "semester 5"]
}

def get_all_subject_names(course_data):
    """Dynamically gets all subject names and their abbreviations from the course data."""
    subjects = set()  # Use a set to automatically handle duplicates
    for sem_info in course_data.get("syllabus", {}).values():
        if isinstance(sem_info, dict):
            for subject in sem_info.get("subjects", []):
                name = subject.get("name", "").lower()
                if not name:
                    continue
                
                # Add the full name, removing content in parentheses for a cleaner match
                full_name = re.sub(r'\(.*\)', '', name).strip()
                subjects.add(full_name)
                
                # Add abbreviations found in parentheses
                abbreviations = re.findall(r'\((.*?)\)', name)
                for abbr in abbreviations:
                    subjects.add(abbr.strip().lower())

    return list(subjects)


def find_subject_in_query(query, subjects_list):
    """Finds the longest matching subject in the query to be more precise."""
    # --- BUG FIX IMPLEMENTED HERE ---
    # Sort subjects by length (desc) and check simple 'in' condition
    sorted_subjects = sorted(subjects_list, key=len, reverse=True)
    for subject in sorted_subjects:
        if subject in query:
            return subject
    return None


def find_semester_in_query(query, semester_map):
    for sem_key, keywords in semester_map.items():
        for keyword in keywords:
            if keyword in query:
                return sem_key
    return None


def get_detail_from_subject(subject_data, detail_keyword):
    """Extracts a specific detail from subject data."""
    subject_name = subject_data.get("name", "this subject")
    if detail_keyword in ["practical", "practicals"]:
        practicals = subject_data.get("practicals", [])
        return f"The practicals for {subject_name} are: " + ", ".join(practicals) if practicals else f"No practicals are listed for {subject_name}."
    if detail_keyword in ["credit", "credits"]:
        credits = subject_data.get("credits", {})
        return f"{subject_name} has {credits.get('total', 'N/A')} total credits." if credits else f"Credit information is not available for {subject_name}."
    if detail_keyword in ["reference", "reference books", "books"]:
        books = subject_data.get("reference_books", [])
        return f"The reference books for {subject_name} are: " + ", ".join(books) if books else f"No reference books are listed for {subject_name}."
    if detail_keyword in ["topic", "topics"]:
        topics = subject_data.get("topics", [])
        return f"The topics for {subject_name} are: " + ", ".join(topics) if topics else f"No topics are listed for {subject_name}."
    return f"I couldn't find the specific '{detail_keyword}' details for {subject_name}."


def handle_syllabus_query(data):
    """Handles all syllabus and course related queries with conversational state."""
    query = data.get("question", "").lower().strip()
    course_data = data.get("course_data", {})
    state = data.get("conversation_state")
    
    subjects_list = get_all_subject_names(course_data)
    
    # Prevent asking about semesters we don’t have
    if "sem 2" in query or "sem 4" in query or "sem 6" in query:
        return {"answer": "I'm sorry, I only have syllabus data available for Semesters 1, 3, and 5 right now.", "new_state": "DEFAULT"}
    
    # If we’re waiting for subject after asking about detail
    if state == "AWAITING_SUBJECT_INFO":
        original_detail = data.get("original_detail")
        subject_name = find_subject_in_query(query, subjects_list)
        if subject_name:
            for sem_info in course_data.get("syllabus", {}).values():
                if isinstance(sem_info, dict):
                    for subject in sem_info.get("subjects", []):
                        if subject_name in subject.get("name", "").lower():
                            answer = get_detail_from_subject(subject, original_detail)
                            return {"answer": answer, "new_state": "DEFAULT"}
        return {"answer": "I still didn't catch a valid subject name. Please try again.", "new_state": "DEFAULT"}

    # Main subject & semester matching
    subject_match = find_subject_in_query(query, subjects_list)
    semester = find_semester_in_query(query, SEMESTER_MAP)
    detail_keyword = next((k for k in ["practical", "credit", "topics", "reference", "books"] if k in query), None)

    if subject_match:
        for sem_info in course_data.get("syllabus", {}).values():
            if isinstance(sem_info, dict):
                for s in sem_info.get("subjects", []):
                    if subject_match in s.get("name", "").lower():
                        if detail_keyword:
                            return {"answer": get_detail_from_subject(s, detail_keyword), "new_state": "DEFAULT"}
                        return {"answer": f"Details for {s.get('name')}:", "data": s, "new_state": "DEFAULT"}

    if semester and detail_keyword:
        return {
            "answer": f"I can get the {detail_keyword} for you. Which subject in {semester} are you asking about?",
            "new_state": "AWAITING_SUBJECT_INFO",
            "original_detail": detail_keyword
        }

    if semester:
        sem_data = course_data.get("syllabus", {}).get(semester, {})
        if sem_data:
            sem_subjects = sem_data.get("subjects", [])
            subject_names = [s.get("name") for s in sem_subjects if s.get("name")]
            return {"answer": f"The subjects in {semester} are: {', '.join(subject_names)}.", "new_state": "DEFAULT"}
        return {"answer": f"Sorry, I couldn't find data for {semester}.", "new_state": "DEFAULT"}

    if detail_keyword:
        return {
            "answer": f"I can get the {detail_keyword} list for you. Which subject are you asking about?",
            "new_state": "AWAITING_SUBJECT_INFO",
            "original_detail": detail_keyword
        }

    return {"answer": "I can help with the syllabus. You can ask about a specific subject or semester.", "new_state": "DEFAULT"}


# ==================================================
# API ROUTE
# ==================================================
@app.route("/syllabus", methods=["POST"])
def syllabus_query():
    data = request.json
    
    course_doc = db.collection("courses").document("DSAI").get()
    course_data = course_doc.to_dict()
    data["course_data"] = course_data
    
    response_data = handle_syllabus_query(data)
    return jsonify(response_data)

# ==================================================
if __name__ == "__main__":
    app.run(debug=True)
