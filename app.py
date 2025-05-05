import streamlit as st
from db import insert_record, fetch_all, db
from firebase_admin import firestore


st.title("ポーカーハンド記録アプリ")
st.subheader("ハンドを入力")
game = st.text_input("ゲーム名を入力してください")
hand = st.text_input("ハンド（例: AKs）")
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
        "game": game,
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


# 指定ゲームのデータを取得
query = db.collection("hands").where("game", "==", game).stream()

st.subheader(f"『{game}』のハンド一覧")
for doc in query:
    r = doc.to_dict()
    st.write(r)
    if st.button(f"🗑 このハンドを削除（{r['hand']}）", key=doc.id):
        doc.reference.delete()
        st.experimental_rerun()



if st.button("🗑 Firestoreの全データを削除（gameあり/なし問わず）", type="primary"):
    st.warning("これはすべての記録を完全に削除します。もう一度押すと実行されます。")
    if st.button("⚠️ 本当に全データを削除する（元に戻せません）"):
        docs = db.collection("hands").stream()
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        st.success(f"すべてのハンド記録を {count} 件 削除しました。")
        st.experimental_rerun()
