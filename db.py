# db.py
import os, json
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_KEY_JSON"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

def insert_record(uid: str, record: dict):
    db.collection("users").document(uid).collection("hands").add(record)

def fetch_by_uid(uid: str) -> list:
    docs = db.collection("users").document(uid).collection("hands").stream()
    return [doc.to_dict() for doc in docs]
