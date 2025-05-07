import streamlit as st
from db import insert_record, db
from google.cloud import firestore
from collections import OrderedDict

st.title("スタッツ解析アプリ")

###########################################################################
# 1. 入力エリア ─── ゲーム名・ハンド・アクション
###########################################################################

all_games_initial = sorted({d.to_dict().get("game", "未分類") for d in db.collection("hands").stream()})
GAME_NEW = "＋ 新規ゲームを追加"
options = [GAME_NEW] + all_games_initial if all_games_initial else [GAME_NEW]

selected_game_opt = st.selectbox("ゲームを選択", options, key="game_select")
if selected_game_opt == GAME_NEW:
    game = st.text_input("新しいゲーム名を入力", key="new_game_input")
else:
    game = selected_game_opt

hand = st.text_input("ハンド（例: 27o）", key="hand_input")
preflop_action = st.selectbox(
    "プリフロップアクション",
    ["フォールド", "CC", "レイズ", "3bet", "3betコール", "4bet"],
    key="preflop_input",
)
multiplayer_type = st.radio(
    "ヘッズアップ or マルチウェイ", ["ヘッズアップ", "マルチウェイ"], key="multi_input"
)

last_raiser = False
position = ""
flop = "なし"
turn = "なし"
river = "なし"
turn_type = ""
river_type = ""

if preflop_action != "フォールド" and multiplayer_type == "ヘッズアップ":
    position = st.selectbox("ポジション", ["IP", "OOP"], key="pos_input")
    last_raiser = st.checkbox("プリフロップで自分が最後にレイズした", key="last_raiser_input")

    flop = st.selectbox(
        "フロップアクション",
        ["なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"],
        key="flop_input",
    )

    if flop not in ["なし", "フォールド"]:
        turn = st.selectbox(
            "ターンアクション",
            ["なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"],
            key="turn_input",
        )
        if turn in ["ベット", "レイズ", "3bet"]:
            turn_type = st.radio("ターンのベットタイプ", ["バリュー", "ブラフ"], key="turn_type")

        if turn not in ["なし", "フォールド"]:
            river = st.selectbox(
                "リバーアクション",
                ["なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"],
                key="river_input",
            )
            if river in ["ベット", "レイズ", "3bet"]:
                river_type = st.radio("リバーのベットタイプ", ["バリュー", "ブラフ"], key="river_type")

if st.button("ハンドを記録する"):
    if not game:
        st.error("ゲーム名を入力してください！")
    elif not hand:
        st.error("ハンドを入力してください！")
    else:
        insert_record({
            "game": game,
            "hand": hand,
            "preflop": preflop_action,
            "multiway": multiplayer_type,
            "position": position,
            "last_raiser": last_raiser,
            "flop": flop,
            "turn": turn,
            "turn_type": turn_type,
            "river": river,
            "river_type": river_type,
            "timestamp": firestore.SERVER_TIMESTAMP,
        })
        st.success("ハンドを保存しました！")
        st.experimental_rerun()

###########################################################################
# 2. 記録済みゲームの表示・削除
###########################################################################

st.subheader("記録済みゲームの表示")
all_docs = list(db.collection("hands").order_by("timestamp", direction="DESCENDING").stream())
ordered_games = list(OrderedDict((d.to_dict().get("game", "未分類"), None) for d in all_docs))

view_game = st.selectbox("表示するゲームを選んでください", ordered_games, key="view_game_select")

docs_view = [d for d in all_docs if d.to_dict().get("game") == view_game]
records = [d.to_dict() for d in docs_view]

col1, col2 = st.columns([2, 1])
with col1:
    btn_del_all = st.button(f"⚠️ 『{view_game}』のすべてのハンドを削除", key="del_all_btn")
with col2:
    confirm_all = st.checkbox("確認", key="confirm_del")

if btn_del_all and confirm_all:
    for d in docs_view:
        d.reference.delete()
    st.success(f"{len(docs_view)} 件のハンドを削除しました！")
    st.experimental_rerun()

with st.expander(f"『{view_game}』のハンド一覧 ({len(records)}件)"):
    for d in docs_view:
        rec = d.to_dict()
        st.write(rec)
        if st.button(f"このハンドを削除（{rec['hand']}）", key=f"del_{d.id}"):
            d.reference.delete()
            st.success("削除しました！")
            st.experimental_rerun()

###########################################################################
# 3. スタッツ解析
###########################################################################

# 3. スタッツ解析 ────────────────────────────────────────────

\###########################################################################

st.subheader(f"『{selected\_game}』の統計")

total = len(records)
if total == 0:
st.info("このゲームの記録がまだありません。")
st.stop()

# ---------- プリフロップ ----------

vpip = sum(1 for r in records if r\["preflop"] not in \["フォールド", ""])
pfr = sum(1 for r in records if r\["preflop"] in \["レイズ", "3bet", "4bet"])
three\_bet = sum(1 for r in records if r\["preflop"] in \["3bet", "4bet"])

st.markdown(f"- **VPIP**: {vpip/total:.1%} ({vpip}/{total})")
st.markdown(f"- **PFR**: {pfr/total:.1%} ({pfr}/{total})")
st.markdown(f"- **3bet%**: {three\_bet/total:.1%} ({three\_bet}/{total})")

# ---------- ポストフロップ ----------

flop\_cb\_ip = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "IP" and r.get("flop") == "ベット")
flop\_cb\_oop = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "OOP" and r.get("flop") == "ベット")
flop\_cb\_ip\_base = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "IP")
flop\_cb\_oop\_base = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "OOP")

turn\_cb\_ip = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "IP" and r.get("turn") == "ベット")
turn\_cb\_oop = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "OOP" and r.get("turn") == "ベット")
turn\_cb\_ip\_base = flop\_cb\_ip\_base
turn\_cb\_oop\_base = flop\_cb\_oop\_base

river\_cb\_ip = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "IP" and r.get("river") == "ベット")
river\_cb\_oop = sum(1 for r in records if r.get("last\_raiser") and r.get("position") == "OOP" and r.get("river") == "ベット")
river\_cb\_ip\_base = flop\_cb\_ip\_base
river\_cb\_oop\_base = flop\_cb\_oop\_base

st.markdown(f"- **Flop CB% (IP)**: {flop\_cb\_ip/flop\_cb\_ip\_base:.1%} ({flop\_cb\_ip}/{flop\_cb\_ip\_base})" if flop\_cb\_ip\_base else "- **Flop CB% (IP)**: なし")
st.markdown(f"- **Flop CB% (OOP)**: {flop\_cb\_oop/flop\_cb\_oop\_base:.1%} ({flop\_cb\_oop}/{flop\_cb\_oop\_base})" if flop\_cb\_oop\_base else "- **Flop CB% (OOP)**: なし")
st.markdown(f"- **Turn CB% (IP)**: {turn\_cb\_ip/turn\_cb\_ip\_base:.1%} ({turn\_cb\_ip}/{turn\_cb\_ip\_base})" if turn\_cb\_ip\_base else "- **Turn CB% (IP)**: なし")
st.markdown(f"- **Turn CB% (OOP)**: {turn\_cb\_oop/turn\_cb\_oop\_base:.1%} ({turn\_cb\_oop}/{turn\_cb\_oop\_base})" if turn\_cb\_oop\_base else "- **Turn CB% (OOP)**: なし")
st.markdown(f"- **River CB% (IP)**: {river\_cb\_ip/river\_cb\_ip\_base:.1%} ({river\_cb\_ip}/{river\_cb\_ip\_base})" if river\_cb\_ip\_base else "- **River CB% (IP)**: なし")
st.markdown(f"- **River CB% (OOP)**: {river\_cb\_oop/river\_cb\_oop\_base:.1%} ({river\_cb\_oop}/{river\_cb\_oop\_base})" if river\_cb\_oop\_base else "- **River CB% (OOP)**: なし")
