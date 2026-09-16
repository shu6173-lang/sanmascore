import pandas as pd
import streamlit as st

st.set_page_config(page_title="三麻スコア計算", page_icon="🀄")

st.title("🀄 三麻専用 スコア・チップ計算")

# --- セッション状態の初期化 ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- 1. ルール設定 ---
st.sidebar.header("⚙️ ルール設定")
chip_rate = st.sidebar.number_input("チップ1枚あたりのpt", value=1.0, step=0.5)

# プレイヤー名の設定（サイドバーで管理）
st.sidebar.subheader("👤 プレイヤー名")
p1_name = st.sidebar.text_input("プレイヤー1", "Aさん")
p2_name = st.sidebar.text_input("プレイヤー2", "Bさん")
p3_name = st.sidebar.text_input("プレイヤー3", "Cさん")

# リセットボタン
if st.sidebar.button("🗑️ データを全リセット", type="secondary"):
    st.session_state.history = []
    st.rerun()

# --- 2. 今回の対局結果の入力 ---
st.subheader(f"📝 第 {len(st.session_state.history) + 1} 半荘の入力")

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    st.markdown(f"**{p1_name}**")
    p1_pt = st.number_input(
        f"ゲームPt", value=0.0, step=1.0, key=f"p1_p_{len(st.session_state.history)}"
    )
    p1_chip = st.number_input(
        f"チップ枚数",
        value=0,
        step=1,
        key=f"p1_c_{len(st.session_state.history)}",
    )

with col2:
    st.markdown(f"**{p2_name}**")
    p2_pt = st.number_input(
        f"ゲームPt", value=0.0, step=1.0, key=f"p2_p_{len(st.session_state.history)}"
    )
    p2_chip = st.number_input(
        f"チップ枚数",
        value=0,
        step=1,
        key=f"p2_c_{len(st.session_state.history)}",
    )

with col3:
    st.markdown(f"**{p3_name}**")
    p3_pt = st.number_input(
        f"ゲームPt", value=0.0, step=1.0, key=f"p3_p_{len(st.session_state.history)}"
    )
    p3_chip = st.number_input(
        f"チップ枚数",
        value=0,
        step=1,
        key=f"p3_c_{len(st.session_state.history)}",
    )

# 入力チェック
total_game_pt = p1_pt + p2_pt + p3_pt
total_chips = p1_chip + p2_chip + p3_chip

if round(total_game_pt, 1) != 0.0:
    st.warning(
        f"⚠️ ゲームPtの合計が 0 になっていません（現在: {total_game_pt:+.1f} pt）"
    )

if total_chips != 0:
    st.info(
        f"💡 チップの合計枚数が 0 になっていません（現在: {total_chips:+d} 枚）"
    )

# --- 3. 結果の追加 ---
if st.button(
    "➕ この半荘の結果を記録する", type="primary", use_container_width=True
):
    record = {
        "半荘": f"第{len(st.session_state.history) + 1}半荘",
        f"{p1_name}": p1_pt,
        f"{p2_name}": p2_pt,
        f"{p3_name}": p3_pt,
        # 内部計算用にチップ情報も保持
        "_p1_chip": p1_chip,
        "_p2_chip": p2_chip,
        "_p3_chip": p3_chip,
    }
    st.session_state.history.append(record)
    st.success(
        f"第 {len(st.session_state.history)} 半荘の結果を記録しました！"
    )
    st.rerun()

# --- 4. 履歴と総合計の表示 ---
if st.session_state.history:
    st.markdown("---")
    st.subheader("📊 総合計スコア")

    # トータル計算（ゲームPt + チップ枚数 × レート）
    p1_sum = sum(
        r[p1_name] + (r["_p1_chip"] * chip_rate)
        for r in st.session_state.history
    )
    p2_sum = sum(
        r[p2_name] + (r["_p2_chip"] * chip_rate)
        for r in st.session_state.history
    )
    p3_sum = sum(
        r[p3_name] + (r["_p3_chip"] * chip_rate)
        for r in st.session_state.history
    )

    totals = [
        {"name": p1_name, "total": p1_sum},
        {"name": p2_name, "total": p2_sum},
        {"name": p3_name, "total": p3_sum},
    ]
    totals.sort(key=lambda x: x["total"], reverse=True)

    t_col1, t_col2, t_col3 = st.columns(3)
    cols = [t_col1, t_col2, t_col3]
    for idx, t in enumerate(totals):
        with cols[idx]:
            st.metric(label=f"{idx+1}位 : {t['name']}", value=f"{t['total']:+.1f} pt")

    # 履歴テーブル（内部データ以外を表示）
    st.subheader("📜 対局履歴")
    df = pd.DataFrame(st.session_state.history)
    # 表示用から内部用カラムを除外
    display_df = df[["半荘", p1_name, p2_name, p3_name]]
    st.dataframe(display_df, use_container_width=True)

    # 1件削除機能
    if st.button("↩️ 最後の半荘を取り消す"):
        st.session_state.history.pop()
        st.rerun()

    # CSVダウンロードボタン
    csv = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="💾 結果をCSVファイルで保存（ダウンロード）",
        data=csv,
        file_name="sanma_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
