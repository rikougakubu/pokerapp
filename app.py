import streamlit as st
from db import insert_record, fetch_all, db

st.title("スタッツ解析アプリ")

# -------------------
# ゲーム名とハンド入力
# -------------------
st.subheader("🎮 ゲーム名とハンドの入力")
game = st.text_input("ゲーム名（例：韓国1−3）")
hand = st.text_input("ハンド（例: AsKs）")
preflop = st.selectbox("プリフロップ", ["CC", "レイズ", "3bet", "3betコール", "4bet"])
position = st.selectbox("ポジション", ["IP", "OOP"])
flop = st.selectbox("フロップアクション", ["ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"])
turn = st.selectbox("ターンアクション", ["ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"])
turn_type = st.radio("ターンのベットタイプ", ["バリュー", "ブラフ"], key="turn_type") if turn in ["ベット", "レイズ", "3bet"] else ""
river = st.selectbox("リバーアクション", ["ベット", "チェック", "レイズ", "3bet", "フォールド", "コール"])
river_type = st.radio("リバーのベットタイプ", ["バリュー", "ブラフ"], key="river_type") if river in ["ベット", "レイズ", "3bet"] else ""
last_raiser = st.checkbox("プリフロップで自分が最後にレイズした")

if st.button("✅ ハンドを記録する"):
    record = {
        "game": game,
        "hand": hand,
        "preflop": preflop,
        "position": position,
        "flop": flop,
        "turn": turn,
        "turn_type": turn_type,
        "river": river,
        "river_type": river_type,
        "last_raiser": last_raiser
    }
    insert_record(record)
    st.success("ハンドを保存しました！")

# -------------------
# ゲーム選択とデータ表示
# -------------------
st.subheader("📂 記録済みゲームの表示")
all_docs = db.collection("hands").stream()
games = sorted(set(doc.to_dict().get("game", "未分類") for doc in all_docs))
selected_game = st.selectbox("表示するゲームを選んでください", games)

query = db.collection("hands").where("game", "==", selected_game).stream()
records = []
st.subheader(f"📝 『{selected_game}』のハンド一覧")
for doc in query:
    r = doc.to_dict()
    records.append(r)
    st.write(r)
    if st.button(f"🗑 このハンドを削除（{r['hand']}）", key=doc.id):
        doc.reference.delete()
        st.success("削除しました！")
        st.experimental_rerun()

# -------------------
# スタッツ解析
# -------------------
st.subheader(f"📊 『{selected_game}』の統計")

total = len(records)
vpip = sum(1 for r in records if r["preflop"] != "3betコール")
pfr = sum(1 for r in records if r["preflop"] in ["レイズ", "3bet", "4bet"])
three_bet = sum(1 for r in records if r["preflop"] in ["3bet", "4bet"])

flop_cb_ip = sum(1 for r in records if r.get("last_raiser") and r["position"] == "IP" and r["flop"] == "ベット")
flop_cb_oop = sum(1 for r in records if r.get("last_raiser") and r["position"] == "OOP" and r["flop"] == "ベット")
flop_cb_ip_base = sum(1 for r in records if r.get("last_raiser") and r["position"] == "IP")
flop_cb_oop_base = sum(1 for r in records if r.get("last_raiser") and r["position"] == "OOP")

turn_bets = [r for r in records if r["turn"] in ["ベット", "レイズ", "3bet"]]
turn_value = sum(1 for r in turn_bets if r.get("turn_type") == "バリュー")

river_bets = [r for r in records if r["river"] in ["ベット", "レイズ", "3bet"]]
river_value = sum(1 for r in river_bets if r.get("river_type") == "バリュー")

check_raise = sum(1 for r in records if r["position"] == "OOP" and r["flop"] == "レイズ")
faced_cb = sum(1 for r in records if r["position"] == "OOP" and r["flop"] in ["チェック", "コール", "レイズ", "フォールド"])

if total == 0:
    st.info("このゲームの記録がまだありません。")
else:
    st.markdown(f"- VPIP: {vpip / total:.1%} ({vpip}/{total})")
    st.markdown(f"- PFR: {pfr / total:.1%} ({pfr}/{total})")
    st.markdown(f"- 3bet%: {three_bet / total:.1%} ({three_bet}/{total})")
    st.markdown(f"- Flop CB% (IP): {flop_cb_ip / flop_cb_ip_base:.1%} ({flop_cb_ip}/{flop_cb_ip_base})" if flop_cb_ip_base else "- Flop CB% (IP): なし")
    st.markdown(f"- Flop CB% (OOP): {flop_cb_oop / flop_cb_oop_base:.1%} ({flop_cb_oop}/{flop_cb_oop_base})" if flop_cb_oop_base else "- Flop CB% (OOP): なし")
    st.markdown(f"- Turn バリュー率: {turn_value / len(turn_bets):.1%} ({turn_value}/{len(turn_bets)})" if turn_bets else "- Turn バリュー率: なし")
    st.markdown(f"- River バリュー率: {river_value / len(river_bets):.1%} ({river_value}/{len(river_bets)})" if river_bets else "- River バリュー率: なし")
    st.markdown(f"- フロップチェックレイズ率（OOP）: {check_raise / faced_cb:.1%} ({check_raise}/{faced_cb})" if faced_cb else "- フロップチェックレイズ率（OOP）: なし")
