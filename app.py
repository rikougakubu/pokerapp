import streamlit as st
import asyncio
from db import insert_hand, fetch_all_hands, init_db

st.set_page_config(page_title="Poker Hand Logger", layout="centered")

async def main():
    await init_db()

    st.title("🃏 ポーカー ハンド記録")

    with st.form("hand_form"):
        hand = st.text_input("ハンド（例: AsKs）")
        preflop = st.selectbox("プリフロップアクション", ["CC", "レイズ", "3bet", "3betコール", "4bet"])
        position = st.radio("ポジション", ["インポジション", "アウトオブポジション"])
        flop = st.selectbox("フロップアクション", ["チェック", "ベット", "レイズ", "3bet"])
        turn = st.selectbox("ターンアクション", ["チェック", "ベット", "レイズ", "3bet"])
        river = st.selectbox("リバーアクション", ["チェック", "ベット", "レイズ", "3bet"])
        submitted = st.form_submit_button("記録")

        if submitted:
            await insert_hand({
                "hand": hand,
                "action_preflop": preflop,
                "position": position,
                "action_flop": flop,
                "action_turn": turn,
                "action_river": river
            })
            st.success("保存しました！")

    st.subheader("📜 ハンド履歴")
    rows = await fetch_all_hands()
    for row in rows:
        st.text(f"[{row.timestamp}] {row.hand} - {row.action_preflop}, {row.position}, {row.action_flop}, {row.action_turn}, {row.action_river}")

asyncio.run(main())
