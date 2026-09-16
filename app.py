import streamlit as st

st.set_page_config(page_title="三麻スコア計算", page_icon="🀄")

st.title("🀄 三麻専用 スコア・チップ計算")

# 1. ルール設定
st.sidebar.header("⚙️ ルール設定")
chip_rate = st.sidebar.number_input("チップ1枚あたりのpt", value=1.0, step=0.5)

# 2. ポイント・チップ入力
st.subheader("📝 対局結果の入力")

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    p1_name = st.text_input("名前", "Aさん", key="p1_n")
    p1_pt = st.number_input(f"{p1_name} のゲームPt", value=0.0, step=1.0, key="p1_p")
    p1_chip = st.number_input(f"{p1_name} のチップ枚数", value=0, step=1, key="p1_c")

with col2:
    p2_name = st.text_input("名前", "Bさん", key="p2_n")
    p2_pt = st.number_input(f"{p2_name} のゲームPt", value=0.0, step=1.0, key="p2_p")
    p2_chip = st.number_input(f"{p2_name} のチップ枚数", value=0, step=1, key="p2_c")

with col3:
    p3_name = st.text_input("名前", "Cさん", key="p3_n")
    p3_pt = st.number_input(f"{p3_name} のゲームPt", value=0.0, step=1.0, key="p3_p")
    p3_chip = st.number_input(f"{p3_name} のチップ枚数", value=0, step=1, key="p3_c")

# 入力チェック（ゲームPtとチップの合計確認）
total_game_pt = p1_pt + p2_pt + p3_pt
total_chips = p1_chip + p2_chip + p3_chip

if round(total_game_pt, 1) != 0.0:
    st.warning(f"⚠️ ゲームPtの合計が 0 になっていません（現在: {total_game_pt:+.1f} pt）")

if total_chips != 0:
    st.info(f"💡 チップの合計枚数が 0 になっていません（現在: {total_chips:+d} 枚）")

# 3. 計算実行
if st.button("📊 スコアを計算する", type="primary", use_container_width=True):
    players = [
        {"name": p1_name, "game_pt": p1_pt, "chip": p1_chip},
        {"name": p2_name, "game_pt": p2_pt, "chip": p2_chip},
        {"name": p3_name, "game_pt": p3_pt, "chip": p3_chip},
    ]

    # ゲームPtが高い順に並び替え
    players.sort(key=lambda x: x["game_pt"], reverse=True)

    st.markdown("---")
    st.subheader("🏆 計算結果")

    for i, p in enumerate(players):
        chip_pt = p["chip"] * chip_rate
        total_pt = p["game_pt"] + chip_pt

        st.markdown(f"### **{i+1}位 : {p['name']}** $\rightarrow$ **{total_pt:+.1f} pt**")
        st.caption(f"内訳 ｜ ゲームPt: {p['game_pt']:+.1f} pt ｜ チップ: {chip_pt:+.1f} pt ({p['chip']}枚)")
