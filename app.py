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
        st.rerun()

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
    st.rerun()

with st.expander(f"『{view_game}』のハンド一覧 ({len(records)}件)"):
    for d in docs_view:
        rec = d.to_dict()
        st.write(rec)
        if st.button(f"このハンドを削除（{rec['hand']}）", key=f"del_{d.id}"):
            d.reference.delete()
            st.success("削除しました！")
            st.rerun()

# -------------------
# スタッツ解析
# -------------------
st.subheader(f"『{selected_game}』の統計")

total = len(records)
vpip = sum(1 for r in records if r.get("preflop") not in ["フォールド", ""])
pfr = sum(1 for r in records if r.get("preflop") in ["レイズ", "3bet", "4bet"])
three_bet = sum(1 for r in records if r.get("preflop") in ["3bet", "4bet"])

flop_cb_ip = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP" and r.get("flop") == "ベット")
flop_cb_oop = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP" and r.get("flop") == "ベット")
flop_cb_ip_base = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP")
flop_cb_oop_base = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP")

# Turn/River CB
turn_cb_ip = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP" and r.get("turn") == "ベット")
turn_cb_oop = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP" and r.get("turn") == "ベット")
turn_cb_ip_base = flop_cb_ip_base
turn_cb_oop_base = flop_cb_oop_base

river_cb_ip = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "IP" and r.get("river") == "ベット")
river_cb_oop = sum(1 for r in records if r.get("last_raiser") and r.get("position") == "OOP" and r.get("river") == "ベット")
river_cb_ip_base = flop_cb_ip_base
river_cb_oop_base = flop_cb_oop_base

# Fold to Turn/River CB
fold_to_turn_cb = sum(1 for r in records if not r.get("last_raiser") and r.get("turn") == "フォールド")
fold_to_river_cb = sum(1 for r in records if not r.get("last_raiser") and r.get("river") == "フォールド")

# WTSD%
wtsd_base = sum(1 for r in records if r.get("flop") not in ["", "フォールド"])
wtsd = sum(1 for r in records if r.get("flop") not in ["", "フォールド"] and r.get("river") not in ["フォールド", ""])

# バリュー比率
turn_bets = [r for r in records if r.get("turn") in ["ベット", "レイズ", "3bet"]]
turn_value = sum(1 for r in turn_bets if r.get("turn_type") == "バリュー")

river_bets = [r for r in records if r.get("river") in ["ベット", "レイズ", "3bet"]]
river_value = sum(1 for r in river_bets if r.get("river_type") == "バリュー")

# チェックレイズ率
check_raise = sum(1 for r in records if r.get("position") == "OOP" and r.get("flop") == "レイズ")
faced_cb = sum(1 for r in records if r.get("position") == "OOP" and r.get("flop") in ["チェック", "コール", "レイズ", "フォールド"])

# 追加統計
turn_bet_after_flop_call_base = sum(1 for r in records if r.get("flop") == "ベット" and r.get("turn") in ["チェック", "フォールド", "ベット", "3bet"])
turn_bet_after_flop_call = sum(1 for r in records if r.get("flop") == "ベット" and r.get("turn") in ["ベット", "3bet"])

turn_call_raise_after_flop_call_base = sum(1 for r in records if r.get("flop") == "コール" and r.get("turn") in ["コール", "レイズ", "フォールド"])
turn_call_raise_after_flop_call = sum(1 for r in records if r.get("flop") == "コール" and r.get("turn") in ["コール", "レイズ"])

river_bet_after_turn_call_base = sum(1 for r in records if r.get("turn") == "ベット" and r.get("river") in ["チェック", "フォールド", "ベット", "3bet"])
river_bet_after_turn_call = sum(1 for r in records if r.get("turn") == "ベット" and r.get("river") in ["ベット", "3bet"])

river_call_raise_after_turn_call_base = sum(1 for r in records if r.get("turn") == "コール" and r.get("river") in ["コール", "レイズ", "フォールド"])
river_call_raise_after_turn_call = sum(1 for r in records if r.get("turn") == "コール" and r.get("river") in ["コール", "レイズ"])

if total == 0:
    st.info("このゲームの記録がまだありません。")
else:
    st.markdown(f"- VPIP: {vpip / total:.1%} ({vpip}/{total})")
    st.markdown(f"- PFR: {pfr / total:.1%} ({pfr}/{total})")
    st.markdown(f"- 3bet%: {three_bet / total:.1%} ({three_bet}/{total})")
    st.markdown(f"- Flop CB% (IP): {flop_cb_ip / flop_cb_ip_base:.1%} ({flop_cb_ip}/{flop_cb_ip_base})" if flop_cb_ip_base else "- Flop CB% (IP): なし")
    st.markdown(f"- Flop CB% (OOP): {flop_cb_oop / flop_cb_oop_base:.1%} ({flop_cb_oop}/{flop_cb_oop_base})" if flop_cb_oop_base else "- Flop CB% (OOP): なし")
    st.markdown(f"- Turn CB% (IP): {turn_cb_ip / turn_cb_ip_base:.1%} ({turn_cb_ip}/{turn_cb_ip_base})" if turn_cb_ip_base else "- Turn CB% (IP): なし")
    st.markdown(f"- Turn CB% (OOP): {turn_cb_oop / turn_cb_oop_base:.1%} ({turn_cb_oop}/{turn_cb_oop_base})" if turn_cb_oop_base else "- Turn CB% (OOP): なし")
    st.markdown(f"- River CB% (IP): {river_cb_ip / river_cb_ip_base:.1%} ({river_cb_ip}/{river_cb_ip_base})" if river_cb_ip_base else "- River CB% (IP): なし")
    st.markdown(f"- River CB% (OOP): {river_cb_oop / river_cb_oop_base:.1%} ({river_cb_oop}/{river_cb_oop_base})" if river_cb_oop_base else "- River CB% (OOP): なし")
    st.markdown(f"- Fold to Turn CB%: {fold_to_turn_cb / total:.1%} ({fold_to_turn_cb}/{total})")
    st.markdown(f"- Fold to River CB%: {fold_to_river_cb / total:.1%} ({fold_to_river_cb}/{total})")
    st.markdown(f"- WTSD%: {wtsd / wtsd_base:.1%} ({wtsd}/{wtsd_base})" if wtsd_base else "- WTSD%: なし")
    st.markdown(f"- Turn バリュー率: {turn_value / len(turn_bets):.1%} ({turn_value}/{len(turn_bets)})" if turn_bets else "- Turn バリュー率: なし")
    st.markdown(f"- River バリュー率: {river_value / len(river_bets):.1%} ({river_value}/{len(river_bets)})" if river_bets else "- River バリュー率: なし")
    st.markdown(f"- フロップチェックレイズ率（OOP）: {check_raise / faced_cb:.1%} ({check_raise}/{faced_cb})" if faced_cb else "- フロップチェックレイズ率（OOP）: なし")
    st.markdown(f"- フロップベット→ターンCB率: {turn_bet_after_flop_call / turn_bet_after_flop_call_base:.1%} ({turn_bet_after_flop_call}/{turn_bet_after_flop_call_base})" if turn_bet_after_flop_call_base else "- フロップコール→ターンCB率: なし")
    st.markdown(f"- フロップコール→ターンコール/レイズ率: {turn_call_raise_after_flop_call / turn_call_raise_after_flop_call_base:.1%} ({turn_call_raise_after_flop_call}/{turn_call_raise_after_flop_call_base})" if turn_call_raise_after_flop_call_base else "- フロップコール→ターンコール/レイズ率: なし")
    st.markdown(f"- ターンベット→リバーCB率: {river_bet_after_turn_call / river_bet_after_turn_call_base:.1%} ({river_bet_after_turn_call}/{river_bet_after_turn_call_base})" if river_bet_after_turn_call_base else "- ターンコール→リバーCB率: なし")
    st.markdown(f"- ターンコール→リバーコール/レイズ率: {river_call_raise_after_turn_call / river_call_raise_after_turn_call_base:.1%} ({river_call_raise_after_turn_call}/{river_call_raise_after_turn_call_base})" if river_call_raise_after_turn_call_base else "- ターンコール→リバーコール/レイズ率: なし")
