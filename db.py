# db.py
import os, json, tempfile
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    key_json = os.environ["FIREBASE_KEY_JSON"]
    cred_dict = json.loads(key_json)
    cred = credentials.Certificate(cred_dict)          # ← dict で直接渡せる
    firebase_admin.initialize_app(cred)

db = firestore.client()

def insert_record(record: dict):
    db.collection("hands").add(record)

def fetch_all() -> list:
    return [doc.to_dict() for doc in db.collection("hands").stream()]
