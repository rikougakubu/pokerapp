# db.py
import os, json
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    key_json = os.environ["FIREBASE_KEY_JSON"]
    cred_dict = json.loads(key_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# UIDを含めて記録
def insert_record(uid: str, record: dict):
    record["uid"] = uid  # 必ずUIDを記録に含める
    db.collection("hands").add(record)

# UIDで絞ってすべて取得
def fetch_by_uid(uid: str) -> list:
    docs = db.collection("hands").where("uid", "==", uid).stream()
    return [doc.to_dict() for doc in docs]
