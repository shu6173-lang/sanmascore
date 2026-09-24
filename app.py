import datetime
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread


st.set_page_config(page_title="三麻スコア計算", page_icon="🀄", layout="wide")

# スマホでは「灰色の入力欄そのもの」を短くして3人分を横に収める
st.markdown("""
<style>
@media (max-width: 700px) {
  .block-container {
    max-width: 100% !important;
    padding-left: 0.35rem !important;
    padding-right: 0.35rem !important;
  }

  .st-key-score_input {
    width: 100% !important;
    max-width: 100% !important;
  }

  .st-key-score_input [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    gap: 0.20rem !important;
    width: 100% !important;
  }

  .st-key-score_input [data-testid="column"] {
    flex: 0 0 31.5% !important;
    width: 31.5% !important;
    min-width: 0 !important;
    max-width: 31.5% !important;
  }

  /* 灰色の数値入力欄をコンパクトにする */
  .st-key-score_input [data-testid="stNumberInput"] {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
  }

  .st-key-score_input [data-testid="stNumberInput"] > div {
    width: 100% !important;
    min-width: 0 !important;
  }

  .st-key-score_input [data-testid="stNumberInput"] input {
    min-width: 0 !important;
    width: 100% !important;
    height: 2.35rem !important;
    padding-left: 1.55rem !important;
    padding-right: 1.55rem !important;
    text-align: center !important;
    font-size: 0.95rem !important;
  }

  /* Streamlit標準の − / ＋ ボタンは残して小さくする */
  .st-key-score_input [data-testid="stNumberInput"] button {
    width: 1.45rem !important;
    min-width: 1.45rem !important;
    height: 2.35rem !important;
    padding: 0 !important;
  }

  .st-key-score_input p {
    margin-bottom: 0.10rem !important;
  }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. パスワード保護設定
# ==========================================
PASSWORD = "maitsukisanma"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🀄 三麻専用 スコア・チップ計算")
    st.subheader("🔒 パスワード認証")
    input_pw = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン", type="primary"):
        if input_pw == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません。")
    st.stop()

# ==========================================
# メインアプリ
# ==========================================

st.title("🀄 三麻専用 スコア・チップ計算")

# --- 1. Googleスプレッドシート接続用関数 ---
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        pk = creds_dict["private_key"]
        pk = pk.replace("\\n", "\n")
        creds_dict["private_key"] = pk

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

@st.cache_data(ttl=0)
def load_data_from_sheet():
    try:
        client = get_gspread_client()
        sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
        sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
        data = sheet.get_all_values()
        
        if not data or len(data) <= 1:
            return {}
            
        rows = data[1:]
        
        history_by_date = {}
        for row in rows:
            if not row or not row[0]:
                continue
            date_str = row[0]
            record = {
                "日付": date_str,
                "半荘": row[1],
                "p1_name": row[2],
                "p1_pt": int(float(row[3])) if row[3] != "" else 0,
                "p1_chip": int(float(row[4])) if row[4] != "" else 0,
                "p2_name": row[5],
                "p2_pt": int(float(row[6])) if row[6] != "" else 0,
                "p2_chip": int(float(row[7])) if row[7] != "" else 0,
                "p3_name": row[8],
                "p3_pt": int(float(row[9])) if row[9] != "" else 0,
                "p3_chip": int(float(row[10])) if row[10] != "" else 0,
            }
            if date_str not in history_by_date:
                history_by_date[date_str] = []
            history_by_date[date_str].append(record)
            
        return history_by_date
    except Exception as e:
        return {}

def append_data_to_sheet(record):
    client = get_gspread_client()
    sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
    sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
    row_list = [
        record["日付"], record["半荘"],
        record["p1_name"], str(record["p1_pt"]), str(record["p1_chip"]),
        record["p2_name"], str(record["p2_pt"]), str(record["p2_chip"]),
        record["p3_name"], str(record["p3_pt"]), str(record["p3_chip"])
    ]
    sheet.append_row(row_list)

def save_all_to_sheet(history_by_date):
    client = get_gspread_client()
    sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
    sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
    
    columns = ["日付", "半荘", "p1_name", "p1_pt", "p1_chip", "p2_name", "p2_pt", "p2_chip", "p3_name", "p3_pt", "p3_chip"]
    sheet.clear()
    sheet.append_row(columns)
    
    for d, recs in history_by_date.items():
        for r in recs:
            row_list = [
                r["日付"], r["半荘"],
                r["p1_name"], str(r["p1_pt"]), str(r["p1_chip"]),
                r["p2_name"], str(r["p2_pt"]), str(r["p2_chip"]),
                r["p3_name"], str(r["p3_pt"]), str(r["p3_chip"])
            ]
            sheet.append_row(row_list)

if "history_by_date" not in st.session_state:
    st.session_state.history_by_date = load_data_from_sheet()

saved_dates = [d for d, records in st.session_state.history_by_date.items() if len(records) > 0]
saved_dates.sort(reverse=True)

# --- 1. ルール設定 & 対局日選択（サイドバー） ---
st.sidebar.header("📅 対局日の選択")

if saved_dates:
    st.sidebar.markdown("**📌 記録済みの対局日**")
    selected_saved_date = st.sidebar.selectbox(
        "記録がある日を選択",
        ["-- カレンダー指定 --"] + [f"🀄 {d} ({len(st.session_state.history_by_date[d])}半荘)" for d in saved_dates],
    )
else:
    selected_saved_date = "-- カレンダー指定 --"

if selected_saved_date != "-- カレンダー指定 --":
    raw_date_str = selected_saved_date.split(" ")[1]
    default_date = datetime.datetime.strptime(raw_date_str, "%Y-%m-%d").date()
else:
    default_date = datetime.date.today()

play_date = st.sidebar.date_input("日付を直接指定", default_date)
date_str = play_date.strftime("%Y-%m-%d")

if date_str not in st.session_state.history_by_date:
    st.session_state.history_by_date[date_str] = []

current_history = st.session_state.history_by_date[date_str]

st.sidebar.markdown("---")
st.sidebar.header("⚙️ ルール設定")

chip_rate = 2
st.sidebar.caption("🪙 チップ1枚 = 2pt（固定）")

st.sidebar.subheader("👤 プレイヤー名")
p1_name = st.sidebar.text_input("プレイヤー1", "自分")
p2_name = st.sidebar.text_input("プレイヤー2", "相手A")
p3_name = st.sidebar.text_input("プレイヤー3", "相手B")

if st.sidebar.button(f"🗑️ {date_str} のデータをリセット", type="secondary"):
    st.session_state.history_by_date[date_str] = []
    save_all_to_sheet(st.session_state.history_by_date)
    st.cache_data.clear()
    st.rerun()

# --- 2. タブによる画面切り替え ---
tab1, tab2, tab3 = st.tabs(["📝 スコア入力・当日結果", "🏆 通算ランキング", "📦 全データダウンロード"])

# ==========================================
# タブ 1: スコア入力 & 当日の成績表示
# ==========================================
with tab1:
    has_records_icon = " 📌(記録あり)" if len(current_history) > 0 else ""
    game_idx = len(current_history)
    st.subheader(f"📝 {date_str}{has_records_icon} ｜ 第 {game_idx + 1} 半荘の入力")

    # 3人分を「ゲームPtの横一列 → チップの横一列」の順に入力
    with st.container(key="score_input"):
        name_cols = st.columns(3)
        for col, name in zip(name_cols, [p1_name, p2_name, p3_name]):
            with col:
                st.markdown(
                    f"<div style='text-align:center;font-weight:700'>{name}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("**🎮 ゲームPt**")
        pt_col1, pt_col2, pt_col3 = st.columns(3)
        with pt_col1:
            p1_pt = st.number_input(
                f"{p1_name} ゲームPt", step=1, value=0, format="%d",
                key=f"p1_p_{date_str}_{game_idx}", label_visibility="collapsed"
            )
        with pt_col2:
            p2_pt = st.number_input(
                f"{p2_name} ゲームPt", step=1, value=0, format="%d",
                key=f"p2_p_{date_str}_{game_idx}", label_visibility="collapsed"
            )
        with pt_col3:
            p3_pt = st.number_input(
                f"{p3_name} ゲームPt", step=1, value=0, format="%d",
                key=f"p3_p_{date_str}_{game_idx}", label_visibility="collapsed"
            )

        st.markdown("**🪙 チップ枚数**")
        chip_col1, chip_col2, chip_col3 = st.columns(3)
        with chip_col1:
            p1_chip = st.number_input(
                f"{p1_name} チップ枚数", step=1, value=0,
                key=f"p1_c_{date_str}_{game_idx}", label_visibility="collapsed"
            )
        with chip_col2:
            p2_chip = st.number_input(
                f"{p2_name} チップ枚数", step=1, value=0,
                key=f"p2_c_{date_str}_{game_idx}", label_visibility="collapsed"
            )
        with chip_col3:
            p3_chip = st.number_input(
                f"{p3_name} チップ枚数", step=1, value=0,
                key=f"p3_c_{date_str}_{game_idx}", label_visibility="collapsed"
            )

    total_pt = p1_pt + p2_pt + p3_pt
    total_chip = p1_chip + p2_chip + p3_chip

    if total_pt != 0 or total_chip != 0:
        st.warning(f"⚠️ 合計が 0 になっていません (ゲームPt合計: {total_pt:+d} / チップ合計: {total_chip:+d}枚)")
    else:
        st.success("✨ 合計が綺麗に 0 になっています！", icon="✅")

    if st.button("➕ この半荘の結果を記録する", type="primary", use_container_width=True):
        if total_pt != 0 or total_chip != 0:
            st.error("エラー：ゲームPtとチップの合計がそれぞれ0になるように調整してください。")
        else:
            record = {
                "日付": date_str,
                "半荘": f"第{game_idx + 1}半荘",
                "p1_name": p1_name,
                "p2_name": p2_name,
                "p3_name": p3_name,
                "p1_pt": p1_pt,
                "p2_pt": p2_pt,
                "p3_pt": p3_pt,
                "p1_chip": p1_chip,
                "p2_chip": p2_chip,
                "p3_chip": p3_chip,
            }
            current_history.append(record)
            append_data_to_sheet(record)
            st.cache_data.clear()
            
            st.success(f"{date_str} の第 {len(current_history)} 半荘の結果を記録しました！（スプレッドシートに保存完了）")
            st.rerun()

    if current_history:
        st.markdown("---")
        st.subheader(f"📊 【{date_str}】の当日スコア")

        players_summary = {}
        for r in current_history:
            for p_idx in [1, 2, 3]:
                p_name = r[f"p{p_idx}_name"]
                if p_name not in players_summary:
                    players_summary[p_name] = {"game_pt": 0, "chip_count": 0}
                players_summary[p_name]["game_pt"] += r[f"p{p_idx}_pt"]
                players_summary[p_name]["chip_count"] += r[f"p{p_idx}_chip"]

        players_data = []
        for name, data in players_summary.items():
            c_pt = data["chip_count"] * chip_rate
            t_pt = data["game_pt"] + c_pt
            players_data.append({
                "name": name,
                "game_pt": data["game_pt"],
                "chip_count": data["chip_count"],
                "chip_pt": c_pt,
                "total_pt": t_pt,
            })

        players_data.sort(key=lambda x: x["total_pt"], reverse=True)

        cols = st.columns(min(len(players_data), 3))
        for idx, p in enumerate(players_data):
            col_idx = idx % len(cols)
            with cols[col_idx]:
                st.metric(
                    label=f"🏆 {idx+1}位 : {p['name']}",
                    value=f"{int(p['total_pt']):+d} pt",
                    delta=f"本日総合計",
                )
                st.caption(
                    f"🎮 **ゲームPt:** {int(p['game_pt']):+d} pt\n\n"
                    f"🪙 **チップPt:** {int(p['chip_pt']):+d} pt ({p['chip_count']:+d}枚)"
                )

        st.subheader(f"📜 【{date_str}】の対局履歴")
        table_data = []
        for r in current_history:
            row = {
                "日付": r["日付"],
                "半荘": r["半荘"],
                f"{r['p1_name']} (Pt)": r["p1_pt"],
                f"{r['p2_name']} (Pt)": r["p2_pt"],
                f"{r['p3_name']} (Pt)": r["p3_pt"],
            }
            table_data.append(row)

        display_df = pd.DataFrame(table_data)
        st.dataframe(display_df, use_container_width=True)

        st.markdown("#### 🗑️ 誤入力した半荘を個別削除")
        delete_cols = st.columns(min(len(current_history), 3))
        for idx, r in enumerate(current_history):
            with delete_cols[idx % len(delete_cols)]:
                if st.button(
                    f"第{idx + 1}半荘を削除",
                    key=f"delete_{date_str}_{idx}",
                    use_container_width=True,
                ):
                    current_history.pop(idx)
                    # 半荘番号を振り直す
                    for j, rec in enumerate(current_history, start=1):
                        rec["半荘"] = f"第{j}半荘"
                    save_all_to_sheet(st.session_state.history_by_date)
                    st.cache_data.clear()
                    st.rerun()

        csv_day = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label=f"💾 {date_str} の結果をCSVで保存",
            data=csv_day,
            file_name=f"sanma_results_{date_str}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ==========================================
# タブ 2: 通算成績ランキング
# ==========================================
with tab2:
    all_records = []
    for d, recs in st.session_state.history_by_date.items():
        all_records.extend(recs)

    if all_records:
        st.subheader("🏆 プレイヤー別 通算成績ランキング")

        stats = {}
        daily_totals = {}
        for r in all_records:
            game_results = [
                (r["p1_name"], int(r["p1_pt"]), int(r["p1_chip"])),
                (r["p2_name"], int(r["p2_pt"]), int(r["p2_chip"])),
                (r["p3_name"], int(r["p3_pt"]), int(r["p3_chip"])),
            ]
            game_results.sort(key=lambda x: x[1], reverse=True)

            for rank_idx, (name, g_pt, chip) in enumerate(game_results, start=1):
                if name not in stats:
                    stats[name] = {
                        "games": 0, "total_game_pt": 0, "total_chips": 0,
                        "r1_count": 0, "r2_count": 0, "r3_count": 0,
                    }
                s = stats[name]
                s["games"] += 1
                s["total_game_pt"] += g_pt
                s["total_chips"] += chip
                if rank_idx == 1:
                    s["r1_count"] += 1
                elif rank_idx == 2:
                    s["r2_count"] += 1
                else:
                    s["r3_count"] += 1

                daily_totals.setdefault(name, {})
                daily_totals[name][r["日付"]] = (
                    daily_totals[name].get(r["日付"], 0) + g_pt + chip * chip_rate
                )

        ranking_list = []
        for name, s in stats.items():
            chip_pt = s["total_chips"] * chip_rate
            total_pt = s["total_game_pt"] + chip_pt
            avg_rank = (
                (s["r1_count"] + s["r2_count"] * 2 + s["r3_count"] * 3) / s["games"]
                if s["games"] else 0
            )
            avg_chip = s["total_chips"] / s["games"] if s["games"] else 0
            day_values = list(daily_totals.get(name, {}).values())
            ranking_list.append({
                "プレイヤー名": name,
                "通算総合Pt": int(total_pt),
                "対局数": s["games"],
                "1着": s["r1_count"],
                "2着": s["r2_count"],
                "3着": s["r3_count"],
                "平均順位": round(avg_rank, 2),
                "平均チップ": round(avg_chip, 2),
                "1日最高Pt": int(max(day_values)) if day_values else 0,
                "1日最低Pt": int(min(day_values)) if day_values else 0,
            })

        ranking_df = pd.DataFrame(ranking_list)
        ranking_df.sort_values(by="通算総合Pt", ascending=False, inplace=True)
        ranking_df.reset_index(drop=True, inplace=True)
        ranking_df.index += 1
        st.dataframe(ranking_df, use_container_width=True)
    else:
        st.info("💡 対局データがまだありません。まずはスコアを入力していくとランキングが表示されます。")

# ==========================================
# タブ 3: 全対局データ（CSV一括出力）
# ==========================================
with tab3:
    all_records = []
    for d, recs in st.session_state.history_by_date.items():
        all_records.extend(recs)

    if all_records:
        st.subheader("📦 全対局データ一覧")
        all_table_data = []
        for r in all_records:
            all_table_data.append({
                "日付": r["日付"],
                "半荘": r["半荘"],
                "P1名": r["p1_name"],
                "P1_Pt": r["p1_pt"],
                "P1_チップ": r["p1_chip"],
                "P2名": r["p2_name"],
                "P2_Pt": r["p2_pt"],
                "P2_チップ": r["p2_chip"],
                "P3名": r["p3_name"],
                "P3_Pt": r["p3_pt"],
                "P3_チップ": r["p3_chip"],
            })
        all_df = pd.DataFrame(all_table_data)
        st.dataframe(all_df, use_container_width=True)

        csv_all = all_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📦 全対局データ（全日程）を一括CSVダウンロード",
            data=csv_all,
            file_name="sanma_results_all.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("📦 保存されているデータはありません。")
