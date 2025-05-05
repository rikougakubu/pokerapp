import streamlit as st
from db import insert_record, fetch_all, db  # ← db も追加！

st.title("ポーカーハンド記録アプリ")

st.subheader("ハンドを入力")
hand = st.text_input("ハンド（例: AsKs）")
preflop = st.selectbox("プリフロップ", ["CC", "レイズ", "3bet", "3betコール", "4bet"])
position = st.selectbox("ポジション", ["IP", "OOP"])
flop = st.selectbox("フロップアクション", ["ベット", "チェック", "レイズ", "3bet"])

turn = st.selectbox("ターンアクション", ["ベット", "チェック", "レイズ", "3bet"])
if turn in ["ベット", "3bet"]:
    turn_type = st.radio("ターンのベットタイプ", ["バリュー", "ブラフ"], key="turn_type")
else:
    turn_type = ""

river = st.selectbox("リバーアクション", ["ベット", "チェック", "レイズ", "3bet"])
if river in ["ベット", "3bet"]:
    river_type = st.radio("リバーのベットタイプ", ["バリュー", "ブラフ"], key="river_type")
else:
    river_type = ""

if st.button("記録する"):
    record = {
        "hand": hand,
        "preflop": preflop,
        "position": position,
        "flop": flop,
        "turn": turn,
        "turn_type": turn_type,
        "river": river,
        "river_type": river_type
    }
    insert_record(record)
    st.success("保存しました！")

st.subheader("保存されたデータ一覧")
data = fetch_all()
for r in data:
    st.write(r)

# データ消去ボタン（Firestore全削除）
if st.button("⚠️ ハンド記録をすべて削除", type="primary"):
    st.warning("確認のためもう一度押してください。")
    if st.button("本当に削除する（元に戻せません）"):
        docs = db.collection("hands").stream()
        for doc in docs:
            doc.reference.delete()
        st.success("すべてのハンド記録を削除しました。")
