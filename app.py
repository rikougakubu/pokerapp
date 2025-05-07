import streamlit as st
from db import insert_record, db
from google.cloud import firestore
from collections import OrderedDict

st.title("スタッツ解析アプリ")

###########################################################################
# 1. 入力エリア ─── ゲーム名・ハンド・アクション
###########################################################################

# --- 既存ゲーム一覧を取得
all_games_initial = sorted({d.to_dict().get("game", "未分類") for d in db.collection("hands").stream()})
GAME_NEW = "＋ 新規ゲームを追加"
options = [GAME_NEW] + all_games_initial if all_games_initial else [GAME_NEW]

# --- ゲーム名の選択／入力
selected_game_opt = st.selectbox("ゲームを選択", options, key="game_select")
if selected_game_opt == GAME_NEW:
    game = st.text_input("新しいゲーム名を入力", key="new_game_input")
else:
    game = selected_game_opt

# --- 基本情報
hand = st.text_input("ハンド（例: 27o）", key="hand_input")
preflop_action = st.selectbox(
    "プリフロップアクション",
    ["フォールド", "CC", "レイズ", "3bet", "3betコール", "4bet"],
    key="preflop_input",
)
multiplayer_type = st.radio(
    "ヘッズアップ or マルチウェイ", ["ヘッズアップ", "マルチウェイ"], key="multi_input"
)

# --- ポストフロップ入力欄（条件付き）
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

# --- 保存ボタン
if st.button("ハンドを記録する"):
    if not game:
        st.error("ゲーム名を入力してください！")
    elif not hand:
        st.error("ハンドを入力してください！")
    else:
        insert_record(
            {
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
            }
        )
        st.success("ハンドを保存しました！")
        st.experimental_rerun()

###########################################################################
# 2. 記録済みゲームの表示・削除
###########################################################################

st.subheader("記録済みゲームの表示")
# 最新更新順で取得
all_docs = list(db.collection("hands").order_by("timestamp", direction="DESCENDING").stream())
ordered_games = list(OrderedDict((d.to_dict().get("game", "未分類"), None) for d in all_docs))

view_game = st.selectbox("表示するゲームを選んでください", ordered_games, key="view_game_select")

docs_view = [d for d in all_docs if d.to_dict().get("game") == view_game]
records = [d.to_dict() for d in docs_view]

# --- ゲーム丸ごと削除
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

# --- 個別削除 & 一覧
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

st.subheader(f"『{view_game}』の統計")

total = len(records)
if total == 0:
    st.info("このゲームの記録がまだありません。")
    st.stop()

# ---------- プリフロップ ----------
vpip = sum(1 for r in records if r.get("preflop") not in ["フォールド", ""])
pfr = sum(1 for r in records if r.get("preflop") in ["レイズ", "3bet", "4bet"])
three_bet = sum(1 for r in records if r.get("preflop") in ["3bet", "4bet"])

st.markdown(f"- **VPIP**: {vpip/total:.1%} ({vpip}/{total})")
st.markdown(f"- **PFR**: {pfr/total:.1%} ({pfr}/{total})")
st.markdown(f"- **3bet%**: {three_bet/total:.1%} ({three_bet}/{total})")

# ---------- ポストフロップ ----------
flop_cb_ip = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP" and r.get("flop") == "ベット")
flop_cb_oop = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP" and r.get("flop") == "ベット")
flop_cb_ip_base = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP")
flop_cb_oop_base = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP")

turn_cb_ip = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP" and r.get("turn") == "ベット")
turn_cb_oop = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP" and r.get("turn") == "ベット")
turn_cb_ip_base = flop_cb_ip_base
turn_cb_oop_base = flop_cb_oop_base

river_cb_ip = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP" and r.get("river") == "ベット")
river_cb_oop = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP" and r.get("river") == "ベット")
river_cb_ip_base = flop_cb_ip_base
river_cb_oop_base = flop_cb_oop_base

st.markdown(
    f"- **Flop CB% (IP)**: {flop_cb_ip/flop_cb_ip_base:.1%} ({flop_cb_ip}/{flop_cb_ip_base})" if flop_cb_ip_base else "- **Flop CB% (IP)**: なし"
)
st.markdown(
    f"- **Flop CB% (OOP)**: {flop_cb_oop/flop_cb_oop_base:.1%} ({flop_cb_oop}/{flop_cb_oop_base})" if flop_cb_oop_base else "- **Flop CB% (OOP)**: なし"
)
st.markdown(
    f"- **Turn CB% (IP)**: {turn_cb_ip/turn_cb_ip_base:.1%} ({turn_cb_ip}/{turn_cb_ip_base})" if turn_cb_ip_base else "- **Turn CB% (IP)**: なし"
)
st.markdown(
    f"- **Turn CB% (OOP)**: {turn_cb_oop/turn_cb_oop_base:.1%} ({turn_cb_oop}/{turn_cb_oop_base})" if turn_cb_oop_base else "- **Turn CB% (OOP)**: なし"
)
st.markdown(
    f"- **River CB% (IP)**: {river_cb_ip/river_cb_ip_base:.1%} ({river_cb_ip}/{river_cb_ip_base})" if river_cb_ip_base else "- **River CB% (IP)**: なし"
)
st.markdown(
    f"- **River CB% (OOP)**: {river_cb_oop/river_cb_oop
