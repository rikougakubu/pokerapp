import streamlit as st
from db import insert_record, db
from google.cloud import firestore  # Firestore サーバータイムスタンプ用

st.title("スタッツ解析アプリ")

###########################################################################
# 1. ゲーム入力フォーム ───────────────────────────────────────────
###########################################################################

# Firestore からゲーム名を取得し、重複を排除したうえで並べ替え
all_docs_initial = db.collection("hands").stream()
all_games_initial = sorted({doc.to_dict().get("game", "未分類") for doc in all_docs_initial})
GAME_NEW = "＋ 新規ゲームを追加"
options = [GAME_NEW] + all_games_initial if all_games_initial else [GAME_NEW]

with st.form("hand-entry", clear_on_submit=False):
    st.subheader("ゲーム名とハンドの入力")

    # 既存ゲーム or 新規ゲーム
    game_select = st.selectbox("ゲームを選択", options, key="game_select")
    if game_select == GAME_NEW:
        game = st.text_input("新しいゲーム名を入力", key="game_input")
    else:
        game = game_select  # 既存ゲーム名

    hand = st.text_input("ハンド（例: 27o）", key="hand_input")
    preflop_action = st.selectbox("プリフロップアクション", [
        "フォールド", "CC", "レイズ", "3bet", "3betコール", "4bet"
    ], key="preflop_input")
    multiplayer_type = st.radio("ヘッズアップ or マルチウェイ", ["ヘッズアップ", "マルチウェイ"], key="multi_input")

    # 詳細アクション
    last_raiser = False
    position = ""
    flop = "なし"
    turn = "なし"
    river = "なし"
    turn_type = ""
    river_type = ""

    if preflop_action != "フォールド" and multiplayer_type == "ヘッズアップ":
        position = st.selectbox("ポジション", ["IP", "OOP"], key="pos_input")
        last_raiser = st.checkbox("プリフロップで自分が最後にレイズした", key="raiser_input")
        flop = st.selectbox("フロップアクション", [
            "なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"
        ], key="flop_input")

        if flop != "フォールド":
            turn = st.selectbox("ターンアクション", [
                "なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"
            ], key="turn_input")
            if turn in ["ベット", "レイズ", "3bet"]:
                turn_type = st.radio("ターンのベットタイプ", ["バリュー", "ブラフ"], key="turn_type_input")

            if turn != "フォールド":
                river = st.selectbox("リバーアクション", [
                    "なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"
                ], key="river_input")
                if river in ["ベット", "レイズ", "3bet"]:
                    river_type = st.radio("リバーのベットタイプ", ["バリュー", "ブラフ"], key="river_type_input")

    submitted = st.form_submit_button("ハンドを記録する")

if submitted:
    # 必須項目チェック
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
            # 更新順ソート用タイムスタンプ
            "timestamp": firestore.SERVER_TIMESTAMP,
        })
        st.success("ハンドを保存しました！")
        st.experimental_rerun()  # 即 UI 更新

###########################################################################
# 2. 記録済みゲームの一覧と削除 ───────────────────────────────
###########################################################################

st.subheader("記録済みゲームの表示")

# 直近に更新したゲームが先頭になるように、タイムスタンプで降順ソート
all_docs = list(db.collection("hands").order_by("timestamp", direction="DESCENDING").stream())
# OrderedDict で重複排除しつつ順序保持
from collections import OrderedDict
ordered_games = list(OrderedDict((doc.to_dict().get("game", "未分類"), None) for doc in all_docs).keys())

selected_game = st.selectbox("表示するゲームを選んでください", ordered_games, key="view_game_select")

docs_for_game = [d for d in all_docs if d.to_dict().get("game") == selected_game]
records = [d.to_dict() for d in docs_for_game]

# ゲーム丸ごと削除
col1, col2 = st.columns([2, 1])
with col1:
    del_all = st.button(f"⚠️ 『{selected_game}』のすべてのハンドを削除", key="del_all_btn")
with col2:
    confirm_all = st.checkbox("確認", key="confirm_del")

if del_all and confirm_all:
    for d in docs_for_game:
        d.reference.delete()
    st.success(f"{len(docs_for_game)} 件のハンドを削除しました！")
    st.experimental_rerun()

# 個別削除 & 一覧
with st.expander(f"『{selected_game}』のハンド一覧({len(records)}件)"):
    for d in docs_for_game:
        r = d.to_dict()
        st.write(r)
        if st.button(f"このハンドを削除（{r['hand']}）", key=f"del_{d.id}"):
            d.reference.delete()
            st.success("削除しました！")
            st.experimental_rerun()

###########################################################################
# 3. スタッツ解析 ────────────────────────────────────────────
###########################################################################

st.subheader(f"『{selected_game}』の統計")

total = len(records)
if total == 0:
    st.info("このゲームの記録がまだありません。")
    st.stop()

# ---------- プリフロップ ----------
vpip = sum(1 for r in records if r["preflop"] not in ["フォールド", ""])
pfr = sum(1 for r in records if r["preflop"] in ["レイズ", "3bet", "4bet"])
three_bet = sum(1 for r in records if r["preflop"] in ["3bet", "4bet"])

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

st.markdown(f"- **Flop CB% (IP)**: {flop_cb_ip/flop_cb_ip_base:.1%} ({flop_cb_ip}/{flop_cb_ip_base})" if flop_cb_ip_base else "- **Flop CB% (IP)**: なし")
st.markdown(f"- **Flop CB% (OOP)**: {flop_cb_oop/flop_cb_oop_base:.1%} ({flop_cb_oop}/{flop_cb_oop_base})" if flop_cb_oop_base else "- **Flop CB% (OOP)**: なし")
st.markdown(f"- **Turn CB% (IP)**: {turn_cb_ip/turn_cb_ip_base:.1%} ({turn_cb_ip}/{turn_cb_ip_base})" if turn_cb_ip_base else "- **Turn CB% (IP)**: なし")
st.markdown(f"- **Turn CB% (OOP)**: {turn_cb_oop/turn_cb_oop_base:.1%} ({turn_cb_oop}/{turn_cb_oop
