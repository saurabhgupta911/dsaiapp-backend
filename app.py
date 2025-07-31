import os
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, jsonify, request

# --- Initialization ---
app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Set your Google AI API key
genai.configure(api_key="AIzaSyDhOjB04vQmZqYfspgw64gxh04re90FkUM")


# --- API Endpoints ---

@app.route("/")
def get_faculty():
    """This endpoint still fetches faculty data from Firestore."""
    try:
        faculty_list = []
        docs = db.collection('Faculty').stream()
        for doc in docs:
            faculty_list.append(doc.to_dict())
        return jsonify(faculty_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=['POST'])
def chat_with_ai():
    """This endpoint is now smarter. It checks for faculty names."""
    try:
        data = request.get_json()
        user_question = data.get('question')

        if not user_question:
            return jsonify({"error": "No question provided"}), 400

        # --- New Logic: Search the database first ---
        final_prompt = user_question
        context_data = None

        # A simple way to check if the user is asking about a known faculty member
        # In a real app, you might search for all faculty names
        if "Dr. Test Name" in user_question:
            # Search Firestore for a specific document
            docs = db.collection('Faculty').where('name', '==', 'Dr. Test Name').limit(1).stream()
            
            for doc in docs:
                context_data = doc.to_dict()
                break # Stop after finding the first match
        
        # If we found data in our database, create a better prompt for the AI
        if context_data:
            final_prompt = f"Using this information: {str(context_data)}, answer the user's question: '{user_question}'"

        # --- Send final prompt to the AI ---
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(final_prompt)
        ai_answer = response.text

        return jsonify({"answer": ai_answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True)





# import os
# import google.generativeai as genai
# import firebase_admin
# from firebase_admin import credentials, firestore
# from flask import Flask, jsonify, request

# # --- Initialization ---
# app = Flask(__name__)

# # Initialize Firebase
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# # Set your Google AI API key
# # IMPORTANT: Replace "YOUR_GOOGLE_API_KEY" with your actual key
# genai.configure(api_key="AIzaSyDhOjB04vQmZqYfspgw64gxh04re90FkUM")


# # --- API Endpoints ---

# @app.route("/")
# def get_faculty():
#     """This endpoint still fetches faculty data from Firestore."""
#     try:
#         faculty_list = []
#         docs = db.collection('Faculty').stream()
#         for doc in docs:
#             faculty_list.append(doc.to_dict())
#         return jsonify(faculty_list)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @app.route("/chat", methods=['POST'])
# def chat_with_ai():
#     """This endpoint now uses the Google Gemini model."""
#     try:
#         data = request.get_json()
#         user_question = data.get('question')

#         if not user_question:
#             return jsonify({"error": "No question provided"}), 400

#         # Send the question to the Gemini API
#         model = genai.GenerativeModel('gemini-1.5-flash-latest')
#         response = model.generate_content(user_question)
        
#         # Get the AI's answer
#         ai_answer = response.text

#         return jsonify({"answer": ai_answer})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# # --- Run the App ---
# if __name__ == "__main__":
#     app.run(debug=True)