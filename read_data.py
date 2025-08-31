import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate("serviceAccountKey.json")
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

db = firestore.client()

collection_name = "courses" 
collection_ref = db.collection(collection_name)

print(f"--- Reading data from '{collection_name}' collection ---")

try:
    docs = collection_ref.stream()
    all_docs_data = []
    for doc in docs:
        doc_data = doc.to_dict()
        all_docs_data.append(doc_data)
    
    print(json.dumps(all_docs_data, indent=2))

except Exception as e:
    print(f"An error occurred: {e}")

print("\n--- End of data ---")