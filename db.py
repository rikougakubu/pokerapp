import firebase_admin
from firebase_admin import credentials, firestore

# Firebase認証（firebase-key.jsonはpoker_app内に配置）
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)

# Firestore クライアントの初期化
db = firestore.client()

# Firestoreにレコードを保存する関数
def insert_record(record: dict):
    db.collection("hands").add(record)

# Firestoreからすべてのレコードを取得する関数
def fetch_all() -> list:
    docs = db.collection("hands").stream()
    return [doc.to_dict() for doc in docs]
