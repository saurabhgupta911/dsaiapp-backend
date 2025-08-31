from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import re

# ---------------------------
# Initialize Flask app
# ---------------------------
app = Flask(__name__)
CORS(app)

# ---------------------------
# Initialize Firebase
# ---------------------------
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# ==================================================
# Subject Detection Helpers
# ==================================================
SUBJECT_MAP = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dbms": "database management system",
    "adbms": "advanced database management system",
    "ds": "data science",
    "dsa": "data structures",
    "bi": "business intelligence",
    "fuzzy": "fuzzy logic",
    "intro_fuzzy": "introduction to fuzzy logic",
    "cloud": "cloud computing",
    "intro_cloud": "introduction to cloud computing",
    "maths": "mathematics for data science",
    "vedic_maths": "vedic mathematics"
}


def normalize_text(text: str) -> str:
    """Lowercase and strip extra spaces for consistent matching."""
    return text.lower().strip()

def detect_subjects(query: str, faculty_data: list) -> list:
    """
    Detect subjects mentioned in the user query.
    Combines SUBJECT_MAP (abbreviations) + Firestore subjects.
    """
    query = normalize_text(query)
    detected_subjects = []

    # Step 1: Check SUBJECT_MAP (abbreviation expansion)
    for key, full_name in SUBJECT_MAP.items():
        if key in query or full_name in query:
            detected_subjects.append(full_name)

    # Step 2: Collect all subjects dynamically from Firestore
    all_subjects = []
    for faculty in faculty_data:
        subjects_field = faculty.get("subjectsTaught") or faculty.get("subjectTaught") or []
        for subj in subjects_field:
            for s in subj.get("subjects", []):
                all_subjects.append(s)

    # Step 3: Match user query against Firestore subjects
    for subj in all_subjects:
        if normalize_text(subj) in query and subj not in detected_subjects:
            detected_subjects.append(subj)

    return list(set(detected_subjects))  # remove duplicates


# ==================================================
# Faculty Query Handler
# ==================================================
def handle_faculty(query: str):
    query = (query or "").lower().strip()

    # ---- Year normalization ----
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

    # ---- Fetch all faculty ----
    faculty_ref = db.collection("Faculty")
    docs = list(faculty_ref.stream())
    faculty_data = [d.to_dict() for d in docs]

    # ---- Detect subjects dynamically ----
    detected_subjects = detect_subjects(query, faculty_data)

    # ---- Build dynamic faculty synonyms ----
    def gen_name_synonyms(full_name: str):
        low = (full_name or "").lower()
        if not low:
            return set()
        parts = [p for p in re.split(r"\s+", low) if p]
        syns = {low}
        if parts:
            syns.add(parts[0])   # first name
            syns.add(parts[-1])  # last name
        honorific_prefixes = ["mr", "mrs", "ms", "miss", "dr", "prof", "professor"]
        honorific_suffixes = ["sir", "ma'am", "mam", "madam"]
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) > 1 else ""
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
        if not nm:
            continue
        canonical = nm.lower()
        for syn in gen_name_synonyms(nm):
            FACULTY_MAP[syn] = canonical

    # Replace synonyms in query
    for syn in sorted(FACULTY_MAP.keys(), key=len, reverse=True):
        query = re.sub(rf"\b{re.escape(syn)}\b", FACULTY_MAP[syn], query)

    # ---- Helpers ----
    def build_faculty_answer(data: dict) -> str:
        name = data.get("name", "Unknown")
        role = data.get("position", "Faculty")
        dept = data.get("department", "DSAI")

        subjects_field = data.get("subjectsTaught") or data.get("subjectTaught") or []
        chunks = []
        for yb in subjects_field:
            ya = yb.get("yearAlias", "")
            subs = ", ".join(yb.get("subjects", []))
            if ya and subs:
                chunks.append(f"{ya}: {subs}")
        detail = "; ".join(chunks) if chunks else "N/A"
        return f"{name} is {role} in {dept} department. Subjects taught: {detail}."

    def find_doc_by_name(canonical_name: str):
        for d in faculty_data:
            if (d.get("name", "").lower()) == canonical_name:
                return d
        return None

    # ---- Step 6: HOD queries (restricted to DSAI) ----
    if "hod" in query:
        for d in faculty_data:
            if str(d.get("position", "")).strip().lower() == "hod":
                dept = str(d.get("department", "")).strip().lower()
                if not dept or "dsai" in dept or "data science" in dept:
                    return f"The HOD of DSAI is {d.get('name')}."
        return "The HOD of DSAI is Sujata Kotian."

    # ---- Step 7: Direct name + year ----
    for canonical_name in set(FACULTY_MAP.values()):
        if canonical_name and canonical_name in query:
            data = find_doc_by_name(canonical_name)
            if data:
                subjects_field = data.get("subjectsTaught") or data.get("subjectTaught") or []
                if year_found:
                    for yb in subjects_field:
                        if yb.get("yearAlias", "").upper() == year_found:
                            subs = ", ".join(yb.get("subjects", []))
                            if subs:
                                return f"{data['name']} is {data.get('position','Faculty')} in {data.get('department','Dept')} department. Subjects taught in {year_found}: {subs}."
                    return f"{data['name']} does not teach any subjects in {year_found}."
                else:
                    return build_faculty_answer(data)

    # ==================================================
    # ✅ Department query → Collect all matches
    # ==================================================
    for dept_query in [d.get("department", "").lower() for d in faculty_data if d.get("department")]:
        if dept_query in query:
            matches = [
                f'{faculty["name"]} works in {faculty["department"]} department.'
                for faculty in faculty_data
                if faculty.get("department", "").lower() == dept_query
            ]
            if matches:
                return " ".join(matches)

    # ==================================================
    # ✅ Subject + Year query (fixed block)
    # ==================================================
    if detected_subjects and year_found:
        matches = []
        for faculty in faculty_data:
            subjects_field = faculty.get("subjectsTaught") or faculty.get("subjectTaught") or []
            for subj in subjects_field:
                if subj.get("yearAlias", "").lower() == year_found.lower():
                    for s in subj["subjects"]:
                        for ds in detected_subjects:
                            if ds.lower() in s.lower():
                                text = f'{faculty["name"]} teaches {s} in {year_found.upper()}.'
                                if text not in matches:   # ✅ prevent duplicates
                                    matches.append(text)

        if matches:
            return " ".join(matches)
        else:
            return f"No one teaches {', '.join(detected_subjects)} in {year_found.upper()}."
     
    # ==================================================
    # Old subject/year fallback
    # ==================================================
    results = []
    for d in faculty_data:
        subjects_field = d.get("subjectsTaught") or d.get("subjectTaught") or []
        for yb in subjects_field:
            ya = yb.get("yearAlias", "").upper()
            subs = [s.lower() for s in yb.get("subjects", [])]

            # Case 1: Year + Subject
            if year_found and detected_subjects:
                for ds in detected_subjects:
                    if ya == year_found and any(ds in s for s in subs):
                        results.append(f"{d['name']} teaches {ds} in {ya}.")

            # Case 2: Only Subject
            elif detected_subjects and not year_found:
                for ds in detected_subjects:
                    if any(ds in s for s in subs):
                        results.append(f"{d['name']} ({ya}): {', '.join(subs)}")

    if results:
        return " ".join(set(results))

    if detected_subjects and year_found:
        return f"No faculty teaches {', '.join(detected_subjects).upper()} in {year_found}."
    elif detected_subjects:
        return f"No faculty found teaching {', '.join(detected_subjects).upper()}."
    elif year_found:
        return f"No faculty found for {year_found}."

    return "Sorry, I couldn't find any matching faculty information."


# ==================================================
# API ROUTE
# ==================================================
@app.route("/faculty", methods=["POST"])
def faculty():
    query = request.json.get("query", "") or request.json.get("question") or ""
    answer = handle_faculty(query)
    return jsonify({"answer": answer})


# ==================================================
if __name__ == "__main__":
    app.run(debug=True)
