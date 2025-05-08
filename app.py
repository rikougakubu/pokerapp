import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval
from firebase_admin import auth

import os, json, streamlit as st
from firebase_admin import auth
from db import insert_record, fetch_by_uid, db     # ★ fetch_by_uid を import
from google.cloud import firestore
from collections import OrderedDict

CLIENT_ID = "366474801487-5g9g8k8333f8jsjv4bd1njpue13rek06.apps.googleusercontent.com"


# ---------------- Google Sign‑in ボタン ----------------
components.html(f"""
<script src="https://accounts.google.com/gsi/client" async defer></script>
<div id="g_id_onload"
     data-client_id="{CLIENT_ID}"
     data-context="signin"
     data-callback="handleCred"
     data-auto_prompt="false"></div>
<div class="g_id_signin" data-type="standard"></div>

<script>
  function handleCred(resp){{
    window.postMessage({{token: resp.credential}}, "*");
  }}
</script>
""", height=120)

# --------------- ID トークン受信と検証 -----------------
token = streamlit_js_eval(
    js_code="""
        window.token = window.token || "";
        window.addEventListener("message", (e) => {
          if (e.data.token) {
            window.token = e.data.token;
          }
        });
        return window.token;
    """,
    key="get_token"
)

if token and "uid" not in st.session_state:
    try:
        info = auth.verify_id_token(token)
        st.session_state["uid"] = info["uid"]
        st.session_state["email"] = info.get("email")
        st.success(f"ログイン成功: {st.session_state['email']}")
    except Exception:
        st.error("トークン検証失敗")

if "uid" not in st.session_state:
    st.warning("Google ボタンでログインしてください")
    st.stop()

uid = st.session_state["uid"]
# ------------------------------------------------------

# ────────────────────────── 認証フェーズ ──────────────────────────
st.title("スタッツ解析アプリ")




if "uid" not in st.session_state:
    st.warning("ログインが必要です")
    st.stop()

uid = st.session_state["uid"]

###########################################################################
# 1. 入力エリア ─── ゲーム名・ハンド・アクション
###########################################################################

# ▼ そのユーザーのレコード全部を一度取得
records_all = fetch_by_uid(uid)

# ゲームリストを作成
all_games_initial = sorted({r.get("game", "未分類") for r in records_all})
GAME_NEW = "＋ 新規ゲームを追加"
options = [GAME_NEW] + all_games_initial if all_games_initial else [GAME_NEW]

selected_game_opt = st.selectbox("ゲームを選択", options, key="game_select")
game = st.text_input(
    "新しいゲーム名を入力" if selected_game_opt == GAME_NEW else "ゲーム名",
    value="" if selected_game_opt == GAME_NEW else selected_game_opt,
    key="game_input",
)

# --- ハンド169通り ---
ranks = list("AKQJT98765432")
hand_opts = [
    r1 + r2 if i == j else r1 + r2 + "s" if i < j else r2 + r1 + "o"
    for i, r1 in enumerate(ranks) for j, r2 in enumerate(ranks)
]
hand = st.selectbox("ハンドを選択", hand_opts, key="hand_select")

preflop_action = st.selectbox(
    "プリフロップアクション",
    ["フォールド", "CC", "レイズ", "3bet", "3betコール", "4bet"],
    key="preflop",
)
multiplayer_type = st.radio(
    "ヘッズアップ or マルチウェイ", ["ヘッズアップ", "マルチウェイ"], key="multi"
)

# --- ポストフロップ入力 ---
last_raiser = False
position = ""
flop = turn = river = "なし"
turn_type = river_type = ""

if preflop_action != "フォールド" and multiplayer_type == "ヘッズアップ":
    position = st.selectbox("ポジション", ["IP", "OOP"])
    last_raiser = st.checkbox("プリフロップで自分が最後にレイズした")

    flop = st.selectbox(
        "フロップアクション",
        ["なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"],
    )

    if flop not in ["なし", "フォールド"]:
        turn = st.selectbox(
            "ターンアクション",
            ["なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"],
        )
        if turn in ["ベット", "レイズ", "3bet"]:
            turn_type = st.radio("ターンのベットタイプ", ["バリュー", "ブラフ"])
        if turn not in ["なし", "フォールド"]:
            river = st.selectbox(
                "リバーアクション",
                ["なし", "ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"],
            )
            if river in ["ベット", "レイズ", "3bet"]:
                river_type = st.radio("リバーのベットタイプ", ["バリュー", "ブラフ"])

# --- 保存 ---
if st.button("ハンドを記録する"):
    if not game:
        st.error("ゲーム名を入力してください")
    else:
        insert_record(
            uid,
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
            },
        )
        st.success("保存しました")
        st.experimental_rerun()

###########################################################################
# 2. 記録済みゲームの表示・削除
###########################################################################

st.subheader("記録済みゲームの表示")

# Firestore ドキュメントを削除操作で使うので再取得（uid フィルタ済み）
user_docs = list(
    db.collection("hands")
    .where("uid", "==", uid)
    .order_by("timestamp", direction="DESCENDING")
    .stream()
)

games_ordered = list(
    OrderedDict((d.to_dict().get("game", "未分類"), None) for d in user_docs)
)

view_game = st.selectbox("表示するゲームを選択", games_ordered, key="view_game")

docs_view = [d for d in user_docs if d.to_dict().get("game") == view_game]
records = [d.to_dict() for d in docs_view]

col1, col2 = st.columns([2, 1])
with col1:
    if st.button(f"⚠️ 『{view_game}』を全部削除"):
        for d in docs_view:
            d.reference.delete()
        st.success("削除しました")
        st.experimental_rerun()

with st.expander(f"『{view_game}』のハンド一覧 ({len(records)}件)"):
    for d in docs_view:
        rec = d.to_dict()
        st.write(rec)
        if st.button(f"このハンドを削除（{rec['hand']}）", key=f"del_{d.id}"):
            d.reference.delete()
            st.success("削除")
            st.experimental_rerun()

###########################################################################
# 3. スタッツ解析（records は uid 限定）
###########################################################################
# 既存のスタッツ計算コードをそのまま利用できます




st.subheader(f"『{view_game}』の統計")
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
