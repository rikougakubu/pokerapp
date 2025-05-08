import os, json, firebase_admin
from firebase_admin import credentials, firestore

# ───────────────────── Firebase Admin 初期化 ─────────────────────
if not firebase_admin._apps:
    key_json = os.getenv("FIREBASE_KEY_JSON")
    if not key_json:
        raise RuntimeError("FIREBASE_KEY_JSON environment variable is not set")
    cred = credentials.Certificate(json.loads(key_json))  # dict を直接渡す
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ─────────────────────  CRUD ヘルパー  ─────────────────────

def insert_record(uid: str, record: dict):
    """ログインユーザー uid に紐付けてレコードを追加"""
    db.collection("hands").add({**record, "uid": uid})


def fetch_records(uid: str) -> list:
    """指定 uid のレコードをすべて取得"""
    docs = db.collection("hands").where("uid", "==", uid).stream()
    return [d.to_dict() for d in docs]


# 管理者用に全件取得を残したい場合はコメントアウトを外す
# def fetch_all() -> list:
#     return [d.to_dict() for d in db.collection("hands").stream()]
