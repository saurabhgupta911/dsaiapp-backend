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

# NOTE: Make sure "serviceAccountKey.json" is in the same directory
cred = credentials.Certificate("serviceAccountKey.json")
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)
db = firestore.client()


# ==================================================
# All Handler Functions (Logic)
# These are the core logic functions for each topic.
# ==================================================

# --- Admin Info Logic ---
LABEL_MAP = {
    "office_hours": "Office Hours",
    "library_hours": "Library Hours",
    "canteen_hours": "Canteen Hours",
    "principal_name": "Principal's Name",
    "general_email": "General College Email",
    "address": "College Address",
    "landline_1": "College Landline",
    "librarian_name": "Librarian's Name",
    "attendance_policy": "Attendance Policy",
    "id_card_policy": "ID Card Policy",
    "anti_ragging_helpline": "Anti-Ragging Helpline Number"
}
KEYWORD_MAP = {
    "office_hours": ["office hours", "office timing", "office open", "office close"],
    "library_hours": ["library hours", "library timing", "library open", "library close"],
    "canteen_hours": ["canteen hours", "canteen timing", "canteen open", "canteen close"],
    "principal_name": ["principal", "principal's name", "head"],
    "general_email": ["email", "college email", "email address"],
    "address": ["address", "location", "where is the college", "where"],
    "landline_1": ["phone", "contact", "landline", "college number"],
    "librarian_name": ["librarian", "librarian's name"],
    "attendance_policy": ["attendance", "attendance policy", "attendance rule"],
    "id_card_policy": ["id card", "identity card", "id policy"],
    "anti_ragging_helpline": [ "anti-ragging ", "helpline","ragging"]
}

def handle_admin_info(query: str, admin_data: list):
    query = query.lower().strip()
    for field, keywords in KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in query:
                for doc in admin_data:
                    if field in doc:
                        label = LABEL_MAP.get(field, field.replace('_', ' '))
                        return f"The {keyword.replace('_', ' ')} is: {doc[field]}."
                return "I couldn't find that specific information."
    if "timing" in query or "hours" in query:
        for doc in admin_data:
            if doc.get("category") == "College Timings":
                return (f"Here are the college timings: "
                        f"* Office Hours: {doc['office_hours']} "
                        f"* Library Hours: {doc['library_hours']} "
                        f"* Canteen Hours: {doc['canteen_hours']}")
    if "contact" in query or "address" in query:
        for doc in admin_data:
            if doc.get("category") == "Contact Information":
                return (f"Here is the contact information: "
                        f"* Principal: {doc['principal_name']} "
                        f"* Address: {doc['address']} "
                        f"* General Email: {doc['general_email']} "
                        f"* Phone: {doc['landline_1']}")
    if "policy" in query or "policies" in query or "rule" in query:
        for doc in admin_data:
            if doc.get("category") == "College Policies":
                return (f"Here are the key college policies: "
                        f"* Attendance: {doc['attendance_policy']} "
                        f"* ID Card: {doc['id_card_policy']} "
                        f"* Anti-Ragging Helpline : {doc['anti_ragging_helpline']}")
    return "Sorry, I can't answer that. I can help with college timings, contact information, and policies."

# --- Library / Books Logic ---
full_library_list = [
    {"title": "Principle of Soft Computing", "author": "SIN SIVANANDAM & SIN DEEPA", "edition": "THIRD", "code": "90911", "category": "Artificial Intelligence"},
    {"title": "Artificial Intelligence: A Modern Approach", "author": "STUART RUSSELL & PETER NORVIG", "edition": "FOURTH", "code": "90912", "category": "Artificial Intelligence"},
    {"title": "Prolog Programming for Artificial Intelligence", "author": "IVAN BRATKO", "edition": "FOURTH", "code": "90913", "category": "Artificial Intelligence"},
    {"title": "Fundamental of Data Science", "author": "SAMULE BURNS", "edition": None, "code": "89820", "category": "Data Science"},
    {"title": "Data Science from Scratch", "author": "JOEL GRUS", "edition": "SECOND", "code": "89821", "category": "Data Science"},
    {"title": "Python for Data Analysis", "author": "WES MCKINNEY", "edition": "SECOND", "code": "89786", "category": "Data Science"},
    {"title": "R for Data Science", "author": "HADLEY WICKHAM & GARRETT GROLEMUND", "edition": None, "code": "89822", "category": "Data Science"},
    {"title": "Essential Math for Data Science", "author": "THOMAS NIELSEN", "edition": None, "code": "89823", "category": "Data Science"},
    {"title": "Business Analytics", "author": "S. CHRISTIAN ALBRIGHT & WAYNE L. WINSTON", "edition": "SIXTH", "code": "89789", "category": "Data Science"},
    {"title": "Practical Statistics for Data Science", "author": "PETER BRUCE, ANDREW BRUCE & PETER GEDECK", "edition": "FOURTH", "code": "89782", "category": "Statistics"},
    {"title": "Statistics for Data Science", "author": "JAMES D MILLER", "edition": "THIRD", "code": "89878", "category": "Statistics"},
    {"title": "All of Statistics: A Concise Course in Statistical Inference", "author": "Larry Wasserman", "edition": "2004", "code": "ST103", "category": "Statistics"},
    {"title": "The Elements of Statistical Learning", "author": "TREVOR HASTIE, ROBERT TIBSHIRANI, JEROME FRIEDMAN", "edition": "SECOND", "code": "ST104", "category": "Statistics"},
    {"title": "Deep Learning", "author": "IAN GOODFELLOW, YOSHUA BENGIO & AARON COURVILLE", "edition": None, "code": "90909", "category": "Machine Learning"},
    {"title": "Pattern Recognition & Machine Learning", "author": "CHRISTOPHER M. BISHOP", "edition": None, "code": "95672", "category": "Machine Learning"},
    {"title": "Hands-On Machine Learning with Scikit-Learn & TensorFlow", "author": "AURELIEN GERON", "edition": "SECOND", "code": "ML101", "category": "Machine Learning"},
    {"title": "Machine Learning: A Probabilistic Perspective", "author": "KEVIN P. MURPHY", "edition": None, "code": "ML102", "category": "Machine Learning"},
    {"title": "Python Machine Learning", "author": "SEBASTIAN RASCHKA & VAHID MIRJALILI", "edition": "THIRD", "code": "ML103", "category": "Machine Learning"},
    {"title": "Core Java Volume I", "author": "CAY HORSTMANN", "edition": "ELEVENTH", "code": "PR101", "category": "Programming"},
    {"title": "Effective Java", "author": "JOSHUA BLOCH", "edition": "THIRD", "code": "PR102", "category": "Programming"},
    {"title": "Python Crash Course", "author": "ERIC MATTHES", "edition": "SECOND", "code": "PR103", "category": "Programming"},
    {"title": "Fluent Python", "author": "LUCIANO RAMALHO", "edition": "SECOND", "code": "PR104", "category": "Programming"},
    {"title": "C++ Primer", "author": "STANLEY LIPPMAN, JOSEÉ LAJOIE, BARBARA MOO", "edition": "FIFTH", "code": "PR105", "category": "Programming"},
    {"title": "Introduction to Algorithms", "author": "THOMAS H. CORMEN et al.", "edition": "FOURTH", "code": "DSA101", "category": "Data Structures & Algorithms"},
    {"title": "Algorithms", "author": "ROBERT SEDGEWICK & KEVIN WAYNE", "edition": "FOURTH", "code": "DSA102", "category": "Data Structures & Algorithms"},
    {"title": "Algorithm Design Manual", "author": "STEVEN SKIENA", "edition": "SECOND", "code": "DSA103", "category": "Data Structures & Algorithms"},
    {"title": "Computer Networking: A Top-Down Approach", "author": "JAMES KUROSE & KEITH ROSS", "edition": "SEVENTH", "code": "CN101", "category": "Computer Networks & Security"},
    {"title": "Cryptography & Network Security", "author": "WILLIAM STALLINGS", "edition": "SEVENTH", "code": "CN102", "category": "Computer Networks & Security"},
    {"title": "Internet of Things: A Hands-On Approach", "author": "ARSHDEEP BAHGA & VIJAY MADISETTI", "edition": None, "code": "CN103", "category": "Computer Networks & Security"},
    {"title": "Digital Image Processing", "author": "RAFAEL C. GONZALEZ & RICHARD E. WOODS", "edition": "FOURTH", "code": "IP101", "category": "Image Processing"},
    {"title": "Computer Graphics with OpenGL", "author": "DONALD HEARN & M. PAULINE BAKER", "edition": "FOURTH", "code": "CG101", "category": "Computer Graphics"},
    {"title": "Database System Concepts", "author": "ABRAHAM SILBERSCHATZ, HENRY KORTH, S. SUDARSHAN", "edition": "SIXTH", "code": "DB101", "category": "Database Systems"},
    {"title": "Fundamentals of Database Systems", "author": "ELMASRI & NAVATHE", "edition": "SEVENTH", "code": "DB102", "category": "Database Systems"},
    {"title": "Data Warehousing in the Real World", "author": "SAM ANAHORY & DENNIS MURRAY", "edition": None, "code": "DB103", "category": "Database Systems"},
    {"title": "Quantitative Aptitude", "author": "R.S. AGGARWAL", "edition": None, "code": "AP101", "category": "Aptitude & Competitive Exams"},
    {"title": "How to Prepare for Quantitative Aptitude for CAT", "author": "ARUN SHARMA", "edition": None, "code": "AP102", "category": "Aptitude & Competitive Exams"},
    {"title": "Verbal & Non-Verbal Reasoning", "author": "R.S. AGGARWAL", "edition": None, "code": "AP103", "category": "Aptitude & Competitive Exams"},
    {"title": "Business Research Methods", "author": "DONALD COOPER & PAMELA SCHINDLER", "edition": "TWELFTH", "code": "BM101", "category": "Business & Management"},
    {"title": "Organizational Behaviour", "author": "STEPHEN P. ROBBINS & TIMOTHY A. JUDGE", "edition": "SEVENTEENTH", "code": "BM102", "category": "Business & Management"},
    {"title": "Marketing Management", "author": "PHILIP KOTLER & KEVIN LANE KELLER", "edition": "FIFTEENTH", "code": "BM103", "category": "Business & Management"},
    {"title": "Human Resource Management", "author": "GARY DESSLER", "edition": "FIFTEENTH", "code": "BM104", "category": "Business & Management"},
    {"title": "Operations Management", "author": "JAY HEIZER & BARRY RENDER", "edition": "TWELFTH", "code": "BM105", "category": "Business & Management"},
    {"title": "Data Mining: Concepts & Techniques", "author": "JIAWEI HAN, MICHELINE KAMBER, JIAN PEI", "edition": "THIRD", "code": "DSC101", "category": "Data Science"},
    {"title": "Big Data: Principles & Best Practices", "author": "PRAMOD ANANTHARAMAN", "edition": None, "code": "DSC102", "category": "Data Science"},
    {"title": "An Introduction to Statistical Learning", "author": "GARETH JAMES, DANIELA WITTEN, TREVOR HASTIE, ROBERT TIBSHIRANI", "edition": "SECOND", "code": "ST105", "category": "Statistics"},
    {"title": "Applied Multivariate Statistical Analysis", "author": "RICHARD JOHNSON & DEAN WICHERN", "edition": "SIXTH", "code": "ST106", "category": "Statistics"},
    {"title": "Time Series Analysis", "author": "ROBERT H. SHUMWAY & DAVID S. STOFFER", "edition": "FOURTH", "code": "ST107", "category": "Statistics"},
    {"title": "Bayesian Data Analysis", "author": "ANDREW GELMAN et al.", "edition": "THIRD", "code": "ST108", "category": "Statistics"},
    {"title": "Introduction to Probability", "author": "DIMITRI BERTSIMAS & JOHN TSITSIKLIS", "edition": None, "code": "ST109", "category": "Statistics"},
    {"title": "Artificial Neural Networks", "author": "BHUVANESWARI PAI", "edition": None, "code": "AI101", "category": "Artificial Intelligence"},
    {"title": "Reinforcement Learning: An Introduction", "author": "RICHARD S. SUTTON & ANDREW G. BARTO", "edition": "SECOND", "code": "AI102", "category": "Artificial Intelligence"},
    {"title": "Knowledge Representation & Reasoning", "author": "RONALD B. Brachman & Hector J. Levesque", "edition": None, "code": "AI103", "category": "Artificial Intelligence"},
    {"title": "Speech & Language Processing", "author": "DAN JURAFSKY & JAMES H. MARTIN", "edition": "THIRD", "code": "AI104", "category": "Artificial Intelligence"},
    {"title": "AI Superpowers", "author": "KAI-FU LEE", "edition": None, "code": "AI105", "category": "Artificial Intelligence"},
    {"title": "Cloud Computing: Principles & Paradigms", "author": "RAJKUMAR BUYYA", "edition": None, "code": "CC101", "category": "Computer Networks & Security"},
    {"title": "Modern Operating Systems", "author": "ANDREW TANENBAUM", "edition": "FOURTH", "code": "OS101", "category": "Computer Networks & Security"},
    {"title": "Operating System Concepts", "author": "ABRAHAM SILBERSCHATZ, PETER B. GALVIN, GREG GAGNE", "edition": "NINTH", "code": "OS102", "category": "Computer Networks & Security"},
    {"title": "Compilers: Principles, Techniques, and Tools", "author": "ALFRED V. AHO, MONICA LAM, RAVI SETHI, JEFFREY D. ULLMAN", "edition": "SECOND", "code": "CS101", "category": "Programming"},
    {"title": "Structure & Interpretation of Computer Programs", "author": "HAROLD ABELSON, GERALD JAY SUSSMMAN", "edition": "SECOND", "code": "CS102", "category": "Programming"},
    {"title": "Clean Code: A Handbook of Agile Software Craftsmanship", "author": "ROBERT C. MARTIN", "edition": None, "code": "CS103", "category": "Programming"},
    {"title": "Design Patterns: Elements of Reusable Object-Oriented Software", "author": "ERICH GAMMA et al.", "edition": None, "code": "CS104", "category": "Programming"},
    {"title": "Refactoring: Improving the Design of Existing Code", "author": "MARTIN FOWLER", "edition": "SECOND", "code": "CS105", "category": "Programming"}
]
LIBRARY_SUBJECT_MAP = {
    "artificial intelligence": ["ai", "a i", "a.i", "artificial intelligence", "soft computing", "pragmatic al", "al robots", "description logic"],
    "machine learning": ["ml", "m l", "m.l", "machine learning", "deep learning", "dl", "d l", "d.l", "transformers", "prml"],
    "data science": ["ds", "d s", "d.s", "data science", "business analytics", "essential math for data science", "python for data analysis", "r for data science"],
    "statistics": ["statistics", "stats", "statistical inference"],
    "programming": ["python", "java", "c++", "core java", "python programming"],
    "database systems": ["database", "dbms", "data warehouse", "data warehousing", "database management system"],
    "data structures & algorithms": ["data structures", "algorithms", "dsa", "computational geometry", "introduction to algorithms"],
    "computer networks & security": ["network", "networking", "security", "iot", "internet of things", "computer security"],
    "image processing": ["image processing", "digital image processing"],
    "computer graphics": ["graphics", "computer graphics"],
    "aptitude & competitive exams": ["aptitude", "cat", "verbal ability", "quantitative aptitude"],
    "business & management": ["business", "management", "marketing", "hr", "organization behaviour", "research methods", "human resource"]
}
ASK_KEYWORDS = [
    "book", "books", "suggest", "recommend", "list", "catalog", "catalogue",
    "library", "any", "have", "available", "find", "get", "show"
]
def normalize_subject(q: str) -> str:
    q = q.lower().strip()
    if ("all" in q and "books" in q) or "full list" in q or "entire library" in q:
        return "all"
    for subject, keys in LIBRARY_SUBJECT_MAP.items():
        for k in keys:
            if re.search(rf"\b{re.escape(k)}\b", q, flags=re.IGNORECASE):
                return subject
    return ""
def match_books_locally(subject: str):
    if subject == "all":
        return full_library_list
    out = []
    s = subject.lower()
    for b in full_library_list:
        if b.get("category", "").lower() == s:
            out.append(b)
    return out

# --- Co-Curricular Activities Logic ---
ACTIVITY_KEYWORDS = {
    "Rotaract Club of Ramniranjan Jhunjhunwala College": ["rotaract", "rcrj"],
    "NSS (National Service Scheme)": ["nss", "national service scheme"],
    "NCC (National Cadet Corps)": ["ncc", "national cadet corps"],
    "DLLE (Lifelong Learning and Extension)": ["dlle", "lifelong learning"]
}
def get_specific_detail(query: str, activity: dict) -> str:
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
    name = activity.get('name', 'N/A')
    description = activity.get('description', 'No description available.')
    benefits_list = activity.get('benefits', [])
    benefits_str = ""
    if benefits_list:
        benefits_str = "Benefits include: " + ", ".join(benefits_list) + "."
    return f"{name}: {description} {benefits_str}"
def handle_cocurricular_query(query: str, activities_data: list):
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

# --- Events Logic ---
EVENT_KEYWORDS = {
    "Inter-Collegiate Departmental Festival 'INCEPTION' 2024": ["2024", "last year"],
    "Inter-Collegiate Departmental Festival 'INCEPTION 2.0'": ["2025", "inception 2.0", "most recent"],
    "Inter-Collegiate Departmental Festival 'INCEPTION' 2026": ["2026", "next", "upcoming", "future", "planned"]
}
def format_schedule(event: dict) -> str:
    name = event.get('name', 'the event')
    schedule_data = event.get('schedule', [])
    if not schedule_data or not schedule_data[0]:
        return f"The schedule for {name} has not been announced yet."
    full_schedule_str = f"Here is the schedule for {name}: "
    for day_info in schedule_data:
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
    count = 0
    for day in event.get('schedule', []):
        if isinstance(day, dict):
            count += len(day.get('activities', []))
    return count
def handle_events_query(query: str, events_data: list):
    query = query.lower().strip()
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
    target_event = None
    for event_name, keywords in EVENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query:
                target_event = next((e for e in events_data if e.get('name') == event_name), None)
                break
        if target_event:
            break
    if target_event:
        for day in target_event.get('schedule', []):
            if isinstance(day, dict):
                for activity in day.get('activities', []):
                    activity_name = ""
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
                        details = []
                        if isinstance(activity, dict):
                            if activity.get('time'): details.append(f"Time: {activity.get('time')}")
                            if activity.get('fee'): details.append(f"Fee: {activity.get('fee')}")
                            if activity.get('venue'): details.append(f"Venue: {activity.get('venue')}")
                        if not details:
                            return f"No specific details like time or fee are listed for '{activity_name}'."
                        return f"For the activity '{activity_name}': " + ", ".join(details)
        if "schedule" in query or "list all" in query or "activities" in query:
            return format_schedule(target_event)
        if "date" in query or "when" in query:
            return f"The dates for {target_event['name']} were {target_event.get('date_summary', 'To be announced')}."
        return (f"{target_event['name']} ({target_event.get('status', 'N/A')}): "
                f"{target_event.get('description') or target_event.get('report_summary', 'No summary available.')}")
    if "2023" in query:
        return "I'm sorry, I don't have any information for events from 2023."
    summary = "We have information on the following fests: " + ", ".join([event.get('name') for event in events_data])
    return summary + ". Which one would you like to know more about?"

# --- Placements Logic ---
def handle_placement_query(query: str, placement_data: list):
    query = query.lower().strip()
    status_doc = next((doc for doc in placement_data if "status_message" in doc), {})
    process_doc = next((doc for doc in placement_data if "steps" in doc), {})
    officer_keywords = ["officer", "coordinator", "contact", "who to contact", "person to contact", "head of placements"]
    if any(k in query for k in officer_keywords):
        officer = status_doc.get("placement_officer", {})
        name = officer.get("name")
        email = officer.get("email")
        if name and email:
            return f"The placement officer is {name}. You can contact them at: {email}."
        else:
            return "The placement officer details have not been announced yet. Please check back later."
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
    general_keywords = ["placement", "status", "career", "job", "opportunities", "internship", "companies", "recruiting"]
    if any(k in query for k in general_keywords):
        return status_doc.get("status_message", "Placement information is not available right now.")
    return "Sorry, I can only answer questions related to placements."

# --- Sessions Logic ---
SESSION_KEYWORDS = {
    "Seminar on Cybersecurity and Safety": ["cybersecurity", "safety", "rajesh mahadik", "rajesh sir"],
    "Bridge Course: Statistics using Excel": ["statistics", "excel", "bridge course", "rahul yadav", "rahul sir"],
    "Session on Cloud Computing": ["cloud computing", "cloud", "abhishek maurya", "abhishek sir"],
    "Ace Your Space: Resume & Job Skills": ["resume", "job skills", "placement training", "darpana more", "darpana mam"]
}
def format_session_details(session: dict) -> str:
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
    query = query.lower().strip()
    target_session_title = None
    for session_title, keywords in SESSION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query:
                target_session_title = session_title
                break
        if target_session_title:
            break
    if target_session_title:
        for session in sessions_data:
            if session.get('title') == target_session_title:
                

                # Check if the user is asking WHO conducted the session
                speaker = session.get('speaker') or session.get('facilitator', 'N/A')
                if any(k in query for k in ["who", "conducted by", "speaker", "facilitator"]):
                    return f"The '{session.get('title')}' was conducted by {speaker}."

                # Check if the user is asking WHEN it was held
                if any(k in query for k in ["when", "date", "time"]):
                    return f"It was held on {session.get('date', 'N/A')} at {session.get('time', 'N/A')}."

                # Check if the user is asking WHERE it was held
                if any(k in query for k in ["where", "venue"]):
                    return f"It was held in {session.get('venue', 'N/A')}."

                # If no specific question is asked, fall back to the full summary
                return format_session_details(session)
                
        return f"I found a match for '{target_session_title}' but couldn't retrieve its details."

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

    if sessions_data:
        summary = "We have information on the following sessions: " + ", ".join([s.get('title', 'Untitled') for s in sessions_data])
        return summary + ". Which of these sessions would you like to know more about?"

    return "Sorry, I couldn't find any information on past sessions."

# --- Courses & Syllabus Logic ---
SYLLABUS_SEMESTER_MAP = {
    "sem1": ["first year", "fy", "sem 1", "semester 1"],
    "sem3": ["second year", "sy", "sem 3", "semester 3"],
    "sem5": ["third year", "ty", "sem 5", "semester 5"]
}
def get_all_subject_names(course_data):
    subjects = set()
    for sem_info in course_data.get("syllabus", {}).values():
        if isinstance(sem_info, dict):
            for subject in sem_info.get("subjects", []):
                name = subject.get("name", "").lower()
                if not name:
                    continue
                full_name = re.sub(r'\(.*\)', '', name).strip()
                subjects.add(full_name)
                abbreviations = re.findall(r'\((.*?)\)', name)
                for abbr in abbreviations:
                    subjects.add(abbr.strip().lower())
    return list(subjects)
def find_subject_in_query(query, subjects_list):
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
    """
    Extracts a specific detail from subject data in a robust way,
    handling cases where data might be missing or empty.
    """
    subject_name = subject_data.get("name", "this subject")

    if detail_keyword in ["practical", "practicals"]:
        practicals = subject_data.get("practicals", [])
        if practicals:
            return f"The practicals for {subject_name} are: " + ", ".join(practicals)
        else:
            return f"No practicals are listed for {subject_name}."

    if detail_keyword in ["credit", "credits"]:
        credits = subject_data.get("credits", {})
        if credits:
            return f"{subject_name} has {credits.get('total', 'N/A')} total credits."
        else:
            return f"Credit information is not available for {subject_name}."

    if detail_keyword in ["reference", "reference books", "books"]:
        books = subject_data.get("reference_books", [])
        if books:
            return f"The reference books for {subject_name} are: " + ", ".join(books)
        else:
            return f"No reference books are listed for {subject_name}."

    if detail_keyword in ["topic", "topics"]:
        topics = subject_data.get("topics", [])
        if topics:
            return f"The topics for {subject_name} are: " + ", ".join(topics)
        else:
            return f"No topics are listed for {subject_name}."
            
    return f"I couldn't find the specific '{detail_keyword}' details for {subject_name}."
def handle_syllabus_query(data):
    query = data.get("question", "").lower().strip()
    course_data = data.get("course_data", {})
    state = data.get("conversation_state")
    subjects_list = get_all_subject_names(course_data)
    if "sem 2" in query or "sem 4" in query or "sem 6" in query:
        return {"answer": "I'm sorry, I only have syllabus data available for Semesters 1, 3, and 5 right now." }
    if state == "AWAITING_SUBJECT_INFO":
        original_detail = data.get("original_detail")
        subject_name = find_subject_in_query(query, subjects_list)
        if subject_name:
            for sem_info in course_data.get("syllabus", {}).values():
                if isinstance(sem_info, dict):
                    for subject in sem_info.get("subjects", []):
                        if subject_name in subject.get("name", "").lower():
                            answer = get_detail_from_subject(subject, original_detail)
                            return {"answer": answer}
        return {"answer": "I still didn't catch a valid subject name. Please try again."}
    subject_match = find_subject_in_query(query, subjects_list)
    semester = find_semester_in_query(query, SYLLABUS_SEMESTER_MAP)
    detail_keyword = next((k for k in ["practical", "credit", "topics", "reference", "books"] if k in query), None)
    if subject_match:
        for sem_info in course_data.get("syllabus", {}).values():
            if isinstance(sem_info, dict):
                for s in sem_info.get("subjects", []):
                    if subject_match in s.get("name", "").lower():
                        if detail_keyword:
                            return {"answer": get_detail_from_subject(s, detail_keyword)}
                        return {"answer": f"Details for {s.get('name')}:", "data": s}
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
            return {"answer": f"The subjects in {semester} are: {', '.join(subject_names)}."}
        return {"answer": f"Sorry, I couldn't find data for {semester}."}
    if detail_keyword:
        return {
            "answer": f"I can get the {detail_keyword} list for you. Which subject are you asking about?",
            "new_state": "AWAITING_SUBJECT_INFO",
            "original_detail": detail_keyword
        }
    return {"answer": "I can help with the syllabus. You can ask about a specific subject or semester."}

# --- Timetables Logic ---
TIMETABLE_SEMESTER_MAP = {
    "First Year - Semester 1": ["first year", "fy", "sem 1", "semester 1"],
    "Second Year - Semester 3": ["second year", "sy", "sem 3", "semester 3"],
    "Third Year - Semester 5": ["third year", "ty", "sem 5", "semester 5"]
}
PROFESSOR_NAMES = ["rahul", "sujata", "mujtaba", "wasif", "darpana", "akash", "shweta", "deepak"]
def format_day_schedule(day: str, schedule: dict) -> str:
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
    Finds and formats answers for timetable-related questions, now with day-specific logic.
    """
    query = query.lower().strip()

    if state == "AWAITING_YEAR_CLARIFICATION":
        full_query = f"{original_query} for {query}"
        return handle_timetable_query(full_query, timetables_data)

    target_semester_name = None
    for sem_name, keywords in TIMETABLE_SEMESTER_MAP.items():
        for keyword in keywords:
            if keyword in query:
                target_semester_name = sem_name
                break
        if target_semester_name:
            break

    target_prof = None
    for prof in PROFESSOR_NAMES:
        if prof in query:
            target_prof = prof
            break
    
    # This is the main block for handling professor schedules
    if target_prof and target_semester_name:
        target_timetable = next((tt for tt in timetables_data if tt.get('semester_name') == target_semester_name), {})
        
        # --- NEW LOGIC TO DETECT A SPECIFIC DAY ---
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        target_day = next((day for day in days_of_week if day in query), None)

        # SCENARIO 1: User asked for a specific day's schedule
        if target_day:
            day_schedule = target_timetable.get("schedule", {}).get(target_day.title(), {})
            prof_lectures_on_day = []
            lectures = day_schedule.get("lectures") or day_schedule.get("lecture", [])
            for lecture in lectures:
                if isinstance(lecture, dict) and lecture.get("professor", "").lower() == target_prof:
                    prof_lectures_on_day.append(f"{lecture.get('subject')} at {lecture.get('time')}")
            
            if prof_lectures_on_day:
                return f"Yes, on {target_day.title()}, Prof. {target_prof.title()} has the following lecture(s) for {target_semester_name}: {', '.join(prof_lectures_on_day)}."
            else:
                return f"No, Prof. {target_prof.title()} has no lectures scheduled on {target_day.title()} for {target_semester_name}."

        # SCENARIO 2: User did not ask for a specific day, so give the full weekly schedule
        else:
            prof_schedule = []
            for day, day_schedule in target_timetable.get("schedule", {}).items():
                lectures = day_schedule.get("lectures") or day_schedule.get("lecture", [])
                for lecture in lectures:
                    if isinstance(lecture, dict) and lecture.get("professor", "").lower() == target_prof:
                        prof_schedule.append(f"on {day}: {lecture.get('subject')} at {lecture.get('time')}")
            
            if prof_schedule:
                return f"For {target_semester_name}, Prof. {target_prof.title()}'s full weekly schedule is: " + ", ".join(prof_schedule) + "."
            else:
                return f"Prof. {target_prof.title()} has no lectures for {target_semester_name}."

    # This part handles requests for a full year's schedule without a professor name
    if target_semester_name:
        target_timetable = next((tt for tt in timetables_data if tt.get('semester_name') == target_semester_name), None)
        if not target_timetable: return f"I'm sorry, I couldn't find timetable data for {target_semester_name}."
        
        schedule = target_timetable.get('schedule', {})
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
        
    # This handles conversational state if not enough info was provided initially
    return {
        "answer": "I can help with the timetable. Please specify a year or a professor's name.",
        "new_state": "AWAITING_YEAR_CLARIFICATION",
        "original_question": query
    }

# --- Faculty Logic ---

SUBJECT_MAP = {
    "ml": "machine learning", "ai": "artificial intelligence", "dbms": "database management system",
    "adbms": "advanced database management system", "ds": "data science", "dsa": "data structures",
    "bi": "business intelligence", "fuzzy": "fuzzy logic", "intro_fuzzy": "introduction to fuzzy logic",
    "cloud": "cloud computing", "intro_cloud": "introduction to cloud computing",
    "maths": "mathematics for data science", "vedic maths": "vedic mathematics", # Corrected key
    "data mining": "Data Mining"
}

def normalize_text(text: str) -> str:
    """Lowercase and strip extra spaces for consistent matching."""
    return text.lower().strip()

def detect_subjects(query: str, faculty_data: list) -> list:
    """Detects subjects mentioned in the user query, ensuring no duplicates."""
    query = normalize_text(query)
    detected_subjects = set()
    for key, full_name in SUBJECT_MAP.items():
        if key.lower() in query or full_name.lower() in query:
            detected_subjects.add(full_name)
    for faculty in faculty_data:
        subjects_field = faculty.get("subjectsTaught") or faculty.get("subjectTaught") or []
        for subj_block in subjects_field:
            for subject_name in subj_block.get("subjects", []):
                if subject_name.lower() in query:
                    detected_subjects.add(subject_name)
    return list(detected_subjects)

def handle_faculty(query: str):
    """Handles all faculty-related questions with robust logic."""
    query = (query or "").lower().strip()
    YEAR_MAP = {
        "fy": "FY", "first year": "FY", "1st year": "FY", "1st": "FY",
        "sy": "SY", "second year": "SY", "2nd year": "SY", "2nd": "SY",
        "ty": "TY", "third year": "TY", "3rd year": "TY", "3rd": "TY"
    }
    year_found = None
    for k, v in YEAR_MAP.items():
        if re.search(rf"\b{k}\b", query):
            year_found = v
            query = re.sub(rf"\b{k}\b", v, query)
            
    faculty_ref = db.collection("Faculty")
    docs = list(faculty_ref.stream())
    faculty_data = [d.to_dict() for d in docs]
    detected_subjects = detect_subjects(query, faculty_data)

    def gen_name_synonyms(full_name: str):
        low = (full_name or "").lower()
        if not low: return set()
        parts = [p for p in re.split(r"\s+", low) if p]
        syns = {low}
        if parts:
            syns.add(parts[0]); syns.add(parts[-1])
        honorific_prefixes = ["mr", "mrs", "ms", "miss", "dr", "prof", "professor"]
        honorific_suffixes = ["sir", "ma'am", "mam", "madam"]
        first = parts[0] if parts else ""; last = parts[-1] if len(parts) > 1 else ""
        for pre in honorific_prefixes:
            if first: syns.add(f"{pre} {first}")
            if last:  syns.add(f"{pre} {last}")
            syns.add(f"{pre} {low}")
        for sfx in honorific_suffixes:
            if first: syns.add(f"{first} {sfx}")
            if last:  syns.add(f"{last} {sfx}")
            syns.add(f"{low} {sfx}")
        return syns
        
    FACULTY_MAP = {}
    for d in docs:
        nm = (d.to_dict().get("name") or "").strip()
        if not nm: continue
        canonical = nm.lower()
        for syn in gen_name_synonyms(nm):
            FACULTY_MAP[syn] = canonical
            
    for syn in sorted(FACULTY_MAP.keys(), key=len, reverse=True):
        query = re.sub(rf"\b{re.escape(syn)}\b", FACULTY_MAP[syn], query)
        
    def build_faculty_answer(data: dict) -> str:
        name = data.get("name", "Unknown")
        role = data.get("position", "Faculty")
        dept = data.get("department", "DSAI")
        subjects_field = data.get("subjectTaught") or []
        chunks = []
        for yb in subjects_field:
            ya = yb.get("yearAlias", "")
            subs = ", ".join(yb.get("subjects", []))
            if ya and subs:
                chunks.append(f"{ya}: {subs}")
        detail = "; ".join(chunks) if chunks else "N/A"
        return f"{name} is a {role} in the {dept} department. Subjects taught: {detail}."
        
    def find_doc_by_name(canonical_name: str):
        for d in faculty_data:
            if (d.get("name", "").lower()) == canonical_name:
                return d
        return None
        
    if "hod" in query:
        for d in faculty_data:
            if str(d.get("position", "")).strip().lower() == "hod":
                dept = str(d.get("department", "")).strip().lower()
                if not dept or "dsai" in dept or "data science" in dept:
                    return f"The HOD of DSAI is {d.get('name')}."
        return "The HOD of DSAI is Sujata Kotian."
        
    # Logic for finding a professor by name
    for canonical_name in set(FACULTY_MAP.values()):
        if canonical_name and canonical_name in query:
            data = find_doc_by_name(canonical_name)
            if data:
                if year_found:
                    for yb in data.get("subjectTaught", []):
                        if yb.get("yearAlias", "").upper() == year_found:
                            subs = ", ".join(yb.get("subjects", []))
                            if subs:
                                return f"{data['name']} teaches the following subjects in {year_found}: {subs}."
                    return f"{data['name']} does not teach any subjects in {year_found}."
                else:
                    return build_faculty_answer(data)

    
    
     # Logic for finding a professor by subject
    if detected_subjects:
        matches = []
        for faculty in faculty_data:
            subjects_field = faculty.get("subjectTaught", []) or []
            for subj_block in subjects_field:
                year_alias = subj_block.get("yearAlias", "").upper()
                if year_found and year_alias != year_found:
                    continue
                for subject_from_db in subj_block.get("subjects", []):
                    for detected_subj in detected_subjects:
                        if detected_subj.lower() in subject_from_db.lower():
                            match_text = f"{faculty['name']} teaches {subject_from_db} in {year_alias}."
                            if match_text not in matches:
                                matches.append(match_text)
        if matches:
            return " ".join(matches)

    # Fallback messages
    if detected_subjects:
        return f"No faculty found teaching {', '.join(detected_subjects).upper()}."
    if year_found:
        return f"No faculty found for {year_found}."

    return "Sorry, I couldn't find any matching faculty information."
    
    
    

# ==================================================
# Smart Chat Endpoint with Intent Detection
# ==================================================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "question" not in data:
        return jsonify({"answer": "Invalid request. Please send a JSON payload with a 'question' key."}), 400

    question = data.get("question", "").lower().strip()
    if not question:
         return jsonify({"answer": "Please ask a question."}), 400

    state = data.get("conversation_state")
    if state == "AWAITING_YEAR_CLARIFICATION":
        original_query = data.get("original_question")
        docs = db.collection("timetables").stream()
        timetables_data = [doc.to_dict() for doc in docs]
        response_data = handle_timetable_query(question, timetables_data, state, original_query)
        if isinstance(response_data, dict):
            return jsonify(response_data)
        return jsonify({"answer": response_data})

    # --- Keyword-based Intent Detection (Corrected Priority) ---
    
    timetable_keywords = ["timetable", "schedule", "lecture", "lectures", "when is my class", "class timing", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    if any(keyword in question for keyword in timetable_keywords):
        state = data.get("conversation_state")
        original_query = data.get("original_question")
        docs = db.collection("timetables").stream()
        timetables_data = [doc.to_dict() for doc in docs]
        response_data = handle_timetable_query(data.get("question"), timetables_data, state, original_query)
        if isinstance(response_data, dict):
            return jsonify(response_data)
        return jsonify({"answer": response_data})

    # PRIORITY: Faculty is checked before Syllabus to handle questions like "subjects of akash sir"
    faculty_keywords = ["faculty", "professor", "teacher", "hod", "sir", "ma'am", "mam", "teaches", "taught by", "sujata", "rahul", "mujtaba", "wasif", "darpana", "akash", "shweta", "deepak"]
    if any(keyword in question for keyword in faculty_keywords):
        answer = handle_faculty(data.get("question"))
        return jsonify({"answer": answer})
        
    syllabus_keywords = ["syllabus", "subject", "credits", "practical", "practicals", "topics", "reference books", "sem 1", "sem 3", "sem 5", "first year", "second year", "third year"]
    if any(keyword in question for keyword in syllabus_keywords):
        course_doc = db.collection("courses").document("DSAI").get()
        course_data = course_doc.to_dict()
        data["course_data"] = course_data
        response_data = handle_syllabus_query(data)
        return jsonify(response_data)

    library_keywords = ["book", "author", "recommend", "suggest", "edition", "catalog", "catalogue"]
    if any(keyword in question for keyword in library_keywords):
        subject = normalize_subject(question)
        if not subject:
            return jsonify({"answer": "Sorry, I couldn't understand the subject you're asking about for the book."})
        books = match_books_locally(subject)
        if not books:
             return jsonify({"answer": f"I looked for {subject} books but couldn't find any right now."})
        return jsonify({"answer": f"Here are some books on {subject}:", "books": books, "subject": subject})
        
    event_keywords = ["event", "fest", "inception", "function", "date", "venue"]
    if any(keyword in question for keyword in event_keywords):
        docs = db.collection("events").stream()
        events_data = [doc.to_dict() for doc in docs]
        answer = handle_events_query(question, events_data)
        clean_answer = answer.replace('\n', ' ').replace('  ', ' ')
        return jsonify({"answer": clean_answer})
        
    cocurricular_keywords = ["cocurricular", "nss", "ncc", "rotaract", "dlle", "club", "join"]
    if any(keyword in question for keyword in cocurricular_keywords):
        docs = db.collection("coCurricularActivities").stream()
        activities_data = [doc.to_dict() for doc in docs]
        answer = handle_cocurricular_query(question, activities_data)
        clean_answer = answer.replace('\n', ' ').replace('  ', ' ')
        return jsonify({"answer": clean_answer})

    placement_keywords = ["placement", "job", "company", "career", "internship", "recruiting", "officer", "resume submission"]
    if any(keyword in question for keyword in placement_keywords):
        docs = db.collection("placementInfo").stream()
        placement_data = [doc.to_dict() for doc in docs]
        answer = handle_placement_query(question, placement_data)
        return jsonify({"answer": answer})
        
    session_keywords = ["session", "seminar", "workshop", "bridge course", "cybersecurity", "resume", "cloud computing"]
    if any(keyword in question for keyword in session_keywords):
        docs = db.collection("sessions").stream()
        sessions_data = [doc.to_dict() for doc in docs]
        answer = handle_sessions_query(question, sessions_data)
        return jsonify({"answer": answer})
        
    docs = db.collection("adminInfo").stream()
    admin_data = [doc.to_dict() for doc in docs]
    answer = handle_admin_info(question, admin_data)
    if "Sorry, I can't answer that" not in answer:
        return jsonify({"answer": answer})

    return jsonify({"answer": "I'm sorry, I'm not sure how to answer that. You can ask me about faculty, library books, college timings, events, or the syllabus."})


# ==================================================
if __name__ == "__main__":
    app.run(debug=True)