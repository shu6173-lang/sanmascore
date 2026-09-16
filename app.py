import streamlit as st

st.set_page_config(page_title="三麻スコア計算", page_icon="🀄")

st.title("🀄 三麻専用 スコア・チップ計算")

# ルール設定
st.sidebar.header("⚙️ ルール設定")
start_pts = st.sidebar.number_input("持ち点", value=35000, step=1000)
return_pts = st.sidebar.number_input("返し点", value=40000, step=1000)
oka_pt = st.sidebar.number_input("オカ（トップ賞/pt）", value=20.0, step=1.0)

st.sidebar.subheader("ウマ設定")
uma_1st = st.sidebar.number_input("1位ウマ", value=15.0)
uma_2nd = st.sidebar.number_input("2位ウマ", value=0.0)
uma_3rd = st.sidebar.number_input("3位ウマ", value=-15.0)

st.sidebar.subheader("チップ設定")
chip_rate = st.sidebar.number_input("チップ1枚あたりのpt", value=1.0, step=0.5)

# 入力画面
st.subheader("📝 対局結果の入力")
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    p1_name = st.text_input("名前", "Aさん", key="p1_n")
    p1_score = st.number_input("素点", value=45000, step=1000, key="p1_s")
    p1_chip = st.number_input("チップ枚数", value=3, step=1, key="p1_c")

with col2:
    p2_name = st.text_input("名前", "Bさん", key="p2_n")
    p2_score = st.number_input("素点", value=35000, step=1000, key="p2_s")
    p2_chip = st.number_input("チップ枚数", value=-1, step=1, key="p2_c")

with col3:
    p3_name = st.text_input("名前", "Cさん", key="p3_n")
    p3_score = st.number_input("素点", value=25000, step=1000, key="p3_s")
    p3_chip = st.number_input("チップ枚数", value=-2, step=1, key="p3_c")

# チェック
total_score = p1_score + p2_score + p3_score
expected_total = start_pts * 3
total_chips = p1_chip + p2_chip + p3_chip

if total_score != expected_total:
    st.warning(f"⚠️ 素点の合計が一致していません（現在: {total_score} / 規定: {expected_total}）")

if total_chips != 0:
    st.info(f"💡 チップの合計枚数が 0 になっていません（現在: {total_chips:+d}枚）")

# 計算実行
if st.button("📊 スコアを計算する", type="primary", use_container_width=True):
    players = [
        {"name": p1_name, "score": p1_score, "chip": p1_chip},
        {"name": p2_name, "score": p2_score, "chip": p2_chip},
        {"name": p3_name, "score": p3_score, "chip": p3_chip},
    ]
    players.sort(key=lambda x: x["score"], reverse=True)
    umas = [uma_1st, uma_2nd, uma_3rd]

    st.markdown("---")
    st.subheader("🏆 計算結果")
    for i, p in enumerate(players):
        raw_pt = (p["score"] - return_pts) / 1000
        uma = umas[i]
        oka = oka_pt if i == 0 else 0.0
        game_pt = raw_pt + uma + oka
        chip_pt = p["chip"] * chip_rate
        total_pt = game_pt + chip_pt

        st.markdown(f"### **{i+1}位 : {p['name']}** $\rightarrow$ **{total_pt:+.1f} pt**")
        st.caption(f"内訳 ｜ ゲーム: {game_pt:+.1f} pt（素点: {raw_pt:+.1f} / ウマ: {uma:+.1f} / オカ: {oka:+.1f}） ｜ チップ: {chip_pt:+.1f} pt ({p['chip']}枚)")