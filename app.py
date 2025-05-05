import streamlit as st
from db import insert_record, fetch_all, db

st.title("ポーカースタッツ解析アプリ")

# -------------------
# ゲーム名入力
# -------------------
st.subheader("ゲーム名とハンドの入力")
game = st.text_input("ゲーム名（例：韓国1−3）")
hand = st.text_input("ハンド（例: 27o）")
preflop = st.selectbox("プリフロップ", ["CC", "レイズ", "3bet", "3betコール", "4bet"])
position = st.selectbox("ポジション", ["IP", "OOP"])
flop = st.selectbox("フロップアクション", ["ベット", "チェック", "レイズ", "3bet"])

turn = st.selectbox("ターンアクション", ["ベット", "チェック", "レイズ", "3bet"])
turn_type = ""
if turn in ["ベット", "3bet"]:
    turn_type = st.radio("ターンのベットタイプ", ["バリュー", "ブラフ"], key="turn_type")

river = st.selectbox("リバーアクション", ["ベット", "チェック", "レイズ", "3bet"])
river_type = ""
if river in ["ベット", "3bet"]:
    river_type = st.radio("リバーのベットタイプ", ["バリュー", "ブラフ"], key="river_type")

if st.button("ハンドを記録する"):
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
    st.success("ハンドを保存しました！")

# -------------------
# ゲーム名一覧の取得と選択
# -------------------
st.subheader("記録済みゲームの表示")

all_docs = db.collection("hands").stream()
games = sorted(set(doc.to_dict().get("game", "未分類") for doc in all_docs))
selected_game = st.selectbox("表示するゲームを選んでください", games)

# -------------------
# 選択ゲームのデータ一覧表示 + 削除
# -------------------
query = db.collection("hands").where("game", "==", selected_game).stream()
st.subheader(f"『{selected_game}』のハンド一覧")
for doc in query:
    r = doc.to_dict()
    st.write(r)
    if st.button(f"このハンドを削除（{r['hand']}）", key=doc.id):
        doc.reference.delete()
        st.success("削除しました！")
        st.experimental_rerun()
