import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="三麻スコア計算", page_icon="🀄")

st.title("🀄 三麻専用 スコア・チップ計算")

# --- セッション状態の初期化 ---
if "history_by_date" not in st.session_state:
    st.session_state.history_by_date = {}

# 過去のデータが存在する日付リストを取得
saved_dates = [d for d, records in st.session_state.history_by_date.items() if len(records) > 0]
saved_dates.sort(reverse=True)

# --- 1. ルール設定 & 対局日選択（サイドバー） ---
st.sidebar.header("📅 対局日の選択")

# データ記録済みの日のクイック選択肢
if saved_dates:
    st.sidebar.markdown("**📌 記録済みの対局日**")
    selected_saved_date = st.sidebar.selectbox(
        "記録がある日を選択",
        ["-- カレンダー指定 --"] + [f"🀄 {d} ({len(st.session_state.history_by_date[d])}半荘)" for d in saved_dates],
    )
else:
    selected_saved_date = "-- カレンダー指定 --"

# カレンダーで直接指定
if selected_saved_date != "-- カレンダー指定 --":
    # 選択肢の文字列（例: "🀄 2026-09-17 (3半荘)"）から日付を取り出す
    raw_date_str = selected_saved_date.split(" ")[1]
    default_date = datetime.datetime.strptime(raw_date_str, "%Y-%m-%d").date()
else:
    default_date = datetime.date.today()

play_date = st.sidebar.date_input("日付を直接指定", default_date)
date_str = play_date.strftime("%Y-%m-%d")

# 選択された日付の履歴リストを取得
if date_str not in st.session_state.history_by_date:
    st.session_state.history_by_date[date_str] = []

current_history = st.session_state.history_by_date[date_str]

# ルールと名前設定
st.sidebar.markdown("---")
st.sidebar.header("⚙️ ルール設定")
chip_rate = st.sidebar.number_input("チップ1枚あたりのpt", value=1.0, step=0.5)

st.sidebar.subheader("👤 プレイヤー名")
p1_name = st.sidebar.text_input("プレイヤー1", "Aさん")
p2_name = st.sidebar.text_input("プレイヤー2", "Bさん")
p3_name = st.sidebar.text_input("プレイヤー3", "Cさん")

# リセットボタン
if st.sidebar.button(f"🗑️ {date_str} のデータをリセット", type="secondary"):
    st.session_state.history_by_date[date_str] = []
    st.rerun()

# --- 2. 今回の対局結果の入力 ---
# 記録がある日の印を表示
has_records_icon = " 📌(記録あり)" if len(current_history) > 0 else ""
st.subheader(f"📝 {date_str}{has_records_icon} ｜ 第 {len(current_history) + 1} 半荘の入力")

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    st.markdown(f"**{p1_name}**")
    p1_pt = st.number_input(
        f"ゲームPt", value=0.0, step=1.0, key=f"p1_p_{date_str}_{len(current_history)}"
    )
    p1_chip = st.number_input(
        f"チップ枚数",
        value=0,
        step=1,
        key=f"p1_c_{date_str}_{len(current_history)}",
    )

with col2:
    st.markdown(f"**{p2_name}**")
    p2_pt = st.number_input(
        f"ゲームPt", value=0.0, step=1.0, key=f"p2_p_{date_str}_{len(current_history)}"
    )
    p2_chip = st.number_input(
        f"チップ枚数",
        value=0,
        step=1,
        key=f"p2_c_{date_str}_{len(current_history)}",
    )

with col3:
    st.markdown(f"**{p3_name}**")
    p3_pt = st.number_input(
        f"ゲームPt", value=0.0, step=1.0, key=f"p3_p_{date_str}_{len(current_history)}"
    )
    p3_chip = st.number_input(
        f"チップ枚数",
        value=0,
        step=1,
        key=f"p3_c_{date_str}_{len(current_history)}",
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
        "日付": date_str,
        "半荘": f"第{len(current_history) + 1}半荘",
        f"{p1_name}": p1_pt,
        f"{p2_name}": p2_pt,
        f"{p3_name}": p3_pt,
        "_p1_chip": p1_chip,
        "_p2_chip": p2_chip,
        "_p3_chip": p3_chip,
    }
    current_history.append(record)
    st.success(
        f"{date_str} の第 {len(current_history)} 半荘の結果を記録しました！"
    )
    st.rerun()

# --- 4. 選択した日付の履歴と総合計の表示 ---
if current_history:
    st.markdown("---")
    st.subheader(f"📊 【{date_str}】の総合計スコア")

    # 集計処理
    players_data = [
        {
            "name": p1_name,
            "game_pt": sum(r[p1_name] for r in current_history),
            "chip_count": sum(r["_p1_chip"] for r in current_history),
        },
        {
            "name": p2_name,
            "game_pt": sum(r[p2_name] for r in current_history),
            "chip_count": sum(r["_p3_chip"] for r in current_history) if p3_name == p["name"] else sum(r["_p2_chip"] for r in current_history),
        },
        {
            "name": p3_name,
            "game_pt": sum(r[p3_name] for r in current_history),
            "chip_count": sum(r["_p3_chip"] for r in current_history),
        },
    ]

    # 正しいインデックスでの集計補正
    players_data[0]["chip_count"] = sum(r["_p1_chip"] for r in current_history)
    players_data[1]["chip_count"] = sum(r["_p2_chip"] for r in current_history)
    players_data[2]["chip_count"] = sum(r["_p3_chip"] for r in current_history)

    for p in players_data:
        p["chip_pt"] = p["chip_count"] * chip_rate
        p["total_pt"] = p["game_pt"] + p["chip_pt"]

    # 総合計順に並び替え
    players_data.sort(key=lambda x: x["total_pt"], reverse=True)

    # カード形式で表示
    cols = st.columns(3)
    for idx, p in enumerate(players_data):
        with cols[idx]:
            st.metric(
                label=f"🏆 {idx+1}位 : {p['name']}",
                value=f"{p['total_pt']:+.1f} pt",
                delta=f"本日総合計",
            )
            st.caption(
                f"🎮 **ゲームPt:** {p['game_pt']:+.1f} pt\n\n"
                f"🪙 **チップPt:** {p['chip_pt']:+.1f} pt ({p['chip_count']}枚)"
            )

    # 履歴テーブル（日付・半荘・各人ゲームPt）
    st.subheader(f"📜 【{date_str}】の対局履歴")
    df = pd.DataFrame(current_history)
    display_df = df[["日付", "半荘", p1_name, p2_name, p3_name]]
    st.dataframe(display_df, use_container_width=True)

    # 1件削除機能
    if st.button("↩️ 最後の半荘を取り消す"):
        current_history.pop()
        st.rerun()

    # CSVダウンロード（その日のみ）
    csv_day = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label=f"💾 {date_str} の結果をCSVで保存",
        data=csv_day,
        file_name=f"sanma_results_{date_str}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# --- 5. 全日程の統合CSV保存機能 ---
all_records = []
for d, recs in st.session_state.history_by_date.items():
    all_records.extend(recs)

if all_records:
    st.markdown("---")
    st.caption("全日程のまとめ出力")
    all_df = pd.DataFrame(all_records)
    cols_to_show = ["日付", "半荘"] + [c for c in all_df.columns if not c.startswith("_") and c not in ["日付", "半荘"]]
    all_display_df = all_df[cols_to_show]
    csv_all = all_display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📦 これまでの全対局データ（全日程）を一括CSVダウンロード",
        data=csv_all,
        file_name="sanma_results_all.csv",
        mime="text/csv",
        use_container_width=True,
    )
