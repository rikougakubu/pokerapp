import streamlit as st
from db import insert_record, fetch_all, db

st.title("スタッツ解析アプリ")

# -------------------
# ゲーム名とハンド入力
# -------------------
st.subheader("ゲーム名とハンドの入力")
game = st.text_input("ゲーム名（例：韓国1−3）")
hand = st.text_input("ハンド（例: 27o）")

preflop_action = st.selectbox("プリフロップアクション", ["フォールド", "CC", "レイズ", "3bet", "3betコール", "4bet"])
multiplayer_type = st.radio("ヘッズアップ or マルチウェイ", ["ヘッズアップ", "マルチウェイ"])

last_raiser = False
position = ""
flop = ""
turn = ""
river = ""
turn_type = ""
river_type = ""

if preflop_action != "フォールド" and multiplayer_type == "ヘッズアップ":
    position = st.selectbox("ポジション", ["IP", "OOP"])
    last_raiser = st.checkbox("プリフロップで自分が最後にレイズした")
    flop = st.selectbox("フロップアクション", ["ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"])

    if flop != "フォールド":
        turn = st.selectbox("ターンアクション", ["ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"])
        if turn in ["ベット", "レイズ", "3bet"]:
            turn_type = st.radio("ターンのベットタイプ", ["バリュー", "ブラフ"], key="turn_type")

        if turn != "フォールド":
            river = st.selectbox("リバーアクション", ["ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"])
            if river in ["ベット", "レイズ", "3bet"]:
                river_type = st.radio("リバーのベットタイプ", ["バリュー", "ブラフ"], key="river_type")

if st.button("ハンドを記録する"):
    record = {
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
        "river_type": river_type
    }
    insert_record(record)
    st.success("ハンドを保存しました！")

# ------------------- ゲーム選択とデータ表示・削除 -------------------
st.subheader("記録済みゲームの表示")
all_docs = db.collection("hands").stream()
games = sorted(set(doc.to_dict().get("game", "未分類") for doc in all_docs))
selected_game = st.selectbox("表示するゲームを選んでください", games)



# 確認付きのゲームごと削除ボタン
confirm_delete = st.button(f"⚠️ 『{selected_game}』のすべてのハンドを削除", type="secondary", use_container_width=True)
confirm = st.checkbox("本当に削除しますか？")
if confirm_delete and confirm:
    docs = db.collection("hands").where("game", "==", selected_game).stream()     
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    st.success(f"{count} 件のハンドを削除しました！")
    st.rerun()

# 一覧と個別削除
query = db.collection("hands").where("game", "==", selected_game).stream()
with st.expander(f"『{selected_game}』のハンド一覧を表示"):
    for doc in query:
        r = doc.to_dict()
        st.write(r)
        if st.button(f"このハンドを削除（{r['hand']}）", key=doc.id):
            doc.reference.delete()
            st.success("削除しました！")
            st.experimental_rerun()

query = db.collection("hands").where("game", "==", selected_game).stream()
records = [doc.to_dict() for doc in query]

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
