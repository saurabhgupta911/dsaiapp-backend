from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# --- Your Full Library Book List (70 books) ---
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
    {"title": "Structure & Interpretation of Computer Programs", "author": "HAROLD ABELSON, GERALD JAY SUSSMAN", "edition": "SECOND", "code": "CS102", "category": "Programming"},
    {"title": "Clean Code: A Handbook of Agile Software Craftsmanship", "author": "ROBERT C. MARTIN", "edition": None, "code": "CS103", "category": "Programming"},
    {"title": "Design Patterns: Elements of Reusable Object-Oriented Software", "author": "ERICH GAMMA et al.", "edition": None, "code": "CS104", "category": "Programming"},
    {"title": "Refactoring: Improving the Design of Existing Code", "author": "MARTIN FOWLER", "edition": "SECOND", "code": "CS105", "category": "Programming"}
]

# --- Synonyms / normalization ---
SUBJECT_MAP = {
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
    
    # special case → all books
    if "all books" in q or "full list" in q or "entire library" in q:
        return "all"
    
    for subject, keys in SUBJECT_MAP.items():
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

@app.route("/ask_book", methods=["POST"])
def ask_book():
    data = request.get_json(force=True) or {}
    question = (data.get("question") or "").strip()
    confirm = data.get("confirm", None)

    subject = normalize_subject(question)
    if not subject:
        return jsonify({
            "answer": "Sorry, I couldn't understand the subject you're asking about. Try AI, ML, Data Science, Statistics, Database, Python, etc."
        }), 200

    # If the user clearly wants books → return directly
    wants_books = any(w in question.lower() for w in ASK_KEYWORDS)
    if wants_books:
        books = match_books_locally(subject)
        if not books:
            return jsonify({"answer": f"I looked for {subject} but couldn't find any books right now."}), 200
        return jsonify({
            "answer": f"Here are {subject} books:",
            "books": books,
            "subject": subject
        }), 200

    # 2-step flow
    if confirm is None:
        return jsonify({
            "answer": f"Yes—reading helps a lot for {subject}. Would you like me to suggest a few books?",
            "subject": subject,
            "next": {"endpoint": "/ask_book", "payload_example": {"question": f"suggest {subject} books", "confirm": True}}
        }), 200

    if confirm is False:
        return jsonify({"answer": "No problem. I'm here if you need help—ask me anytime!"}), 200

    # confirm is True
    books = match_books_locally(subject)
    if not books:
        return jsonify({"answer": f"I looked for {subject} but couldn't find any books right now."}), 200
    return jsonify({
        "answer": f"Here are {subject} books:",
        "books": books,
        "subject": subject
    }), 200

if __name__ == "__main__":
    app.run(debug=True)
