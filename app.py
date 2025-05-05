import streamlit as st
import pandas as pd
import asyncio
from db import init_db, insert_record, fetch_all, HandRecord

# --- DB 初期化 ---
asyncio.run(init_db())

st.title("📋 ポーカー ハンド記録 Webアプリ")

# ===== 入力フォーム =====
with st.form("hand_form"):
    col1, col2 = st.columns(2)
    hand = col1.text_input("ハンド (例: AsKs)")
    preflop = col2.selectbox("プリフロップ", ["CC","RAISE","3BET","3BET_CALL","4BET"])
    position = st.radio("ポジション", ["IP","OOP"], horizontal=True)

    # 各ストリート共通の選択肢
    flop_choices = ["BET","CHECK","RAISE","3BET"] if position=="IP" \
                   else ["BET","CHECK","CALL","3BET"]

    # Flop
    flop_action = st.selectbox("Flop アクション", flop_choices)
    flop_value = None
    if flop_action in {"BET","RAISE","3BET"}:
        flop_value = st.radio("Flop: Value or Bluff?", ["VALUE","BLUFF"], horizontal=True)

    # Turn
    turn_action = st.selectbox("Turn アクション", flop_choices)
    turn_value = None
    if turn_action in {"BET","RAISE","3BET"}:
        turn_value = st.radio("Turn: Value or Bluff?", ["VALUE","BLUFF"], horizontal=True)

    # River
    river_action = st.selectbox("River アクション", flop_choices)
    river_value = None
    if river_action in {"BET","RAISE","3BET"}:
        river_value = st.radio("River: Value or Bluff?", ["VALUE","BLUFF"], horizontal=True)

    submitted = st.form_submit_button("保存")
    if submitted:
        rec = HandRecord(
            hand=hand.upper(), preflop=preflop, position=position,
            flop_action=flop_action, flop_value=flop_value,
            turn_action=turn_action, turn_value=turn_value,
            river_action=river_action, river_value=river_value,
        )
        asyncio.run(insert_record(rec))
        st.success("保存しました ✅")

st.divider()

# ===== 履歴 & 集計 =====
st.subheader("履歴一覧")
rows = asyncio.run(fetch_all())
df = pd.DataFrame(rows)
if df.empty:
    st.info("まだレコードがありません。")
else:
    st.dataframe(df, use_container_width=True, height=300)

    st.subheader("簡易集計 (Flop / Turn / River のアクション比率)")
    for street in ["flop","turn","river"]:
        count = df[f"{street}_action"].value_counts(normalize=True) * 100
        st.write(f"**{street.capitalize()}**")
        st.bar_chart(count)
