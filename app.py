import streamlit as st
from db import insert_record, fetch_all

st.title("ポーカーハンド記録アプリ")

st.subheader("ハンドを入力")
hand = st.text_input("ハンド（例: AsKs）")
preflop = st.selectbox("プリフロップ", ["CC", "レイズ", "3bet", "3betコール", "4bet"])
position = st.selectbox("ポジション", ["IP", "OOP"])
flop = st.selectbox("フロップアクション", ["ベット", "チェック", "レイズ", "3bet"])
turn = st.selectbox("ターンアクション", ["ベット", "チェック", "レイズ", "3bet"])
river = st.selectbox("リバーアクション", ["ベット", "チェック", "レイズ", "3bet"])

if st.button("記録する"):
    record = {
        "hand": hand,
        "preflop": preflop,
        "position": position,
        "flop": flop,
        "turn": turn,
        "river": river
    }
    insert_record(record)
    st.success("保存しました！")

st.subheader("保存されたデータ一覧")
data = fetch_all()
for r in data:
    st.write(r)

