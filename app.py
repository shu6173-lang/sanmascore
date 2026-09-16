import datetime
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

st.set_page_config(page_title="三麻スコア計算", page_icon="🀄", layout="wide")

# --- 0. パスワード認証機能（パスワード固定版） ---
def check_password():
    """パスワードが合っているかチェックする関数"""
    def password_entered():
        if st.session_state["password"] == "maitsukisanma":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.subheader("🔒 このアプリはパスワードが必要です")
        st.text_input(
            "パスワードを入力してください", type="password", on_change=password_entered, key="password"
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 パスワードが間違っています")
        return False
    elif not st.session_state["password_correct"]:
        st.subheader("🔒 このアプリはパスワードが必要です")
        st.text_input(
            "パスワードを入力してください", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 パスワードが間違っています")
        return False
    else:
        return True

if not check_password():
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
                "p1_pt": float(row[3]) if row[3] != "" else 0.0,
                "p1_chip": int(float(row[4])) if row[4] != "" else 0,
                "p2_name": row[5],
                "p2_pt": float(row[6]) if row[6] != "" else 0.0,
                "p2_chip": int(float(row[7])) if row[7] != "" else 0,
                "p3_name": row[8],
                "p3_pt": float(row[9]) if row[9] != "" else 0.0,
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

chip_rate = st.sidebar.number_input("チップ1枚あたりのpt", value=2.0, step=0.5)

st.sidebar.subheader("👤 プレイヤー名")
p1_name = st.sidebar.text_input("プレイヤー1", "Aさん")
p2_name = st.sidebar.text_input("プレイヤー2", "Bさん")
p3_name = st.sidebar.text_input("プレイヤー3", "Cさん")

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
    st.subheader(f"📝 {date_str}{has_records_icon} ｜ 第 {len(current_history) + 1} 半荘の入力")
    st.caption("💡 どの2人分の数値を先に入力しても、最後に残った1人の数値が自動でマイナス計算されて埋まります！")

    game_idx = len(current_history)
    
    # セッションステートの初期化
    for p_num in [1, 2, 3]:
        if f"p{p_num}_p_{date_str}_{game_idx}" not in st.session_state:
            st.session_state[f"p{p_num}_p_{date_str}_{game_idx}"] = 0.0
        if f"p{p_num}_c_{date_str}_{game_idx}" not in st.session_state:
            st.session_state[f"p{p_num}_c_{date_str}_{game_idx}"] = 0

    # 【重要】ウィジェットを描画する「前」に自動計算・書き換えを行っておく
    points_list = [
        (1, st.session_state[f"p1_p_{date_str}_{game_idx}"], st.session_state[f"p1_c_{date_str}_{game_idx}"]),
        (2, st.session_state[f"p2_p_{date_str}_{game_idx}"], st.session_state[f"p2_c_{date_str}_{game_idx}"]),
        (3, st.session_state[f"p3_p_{date_str}_{game_idx}"], st.session_state[f"p3_c_{date_str}_{game_idx}"]),
    ]
    
    non_zero_items = [item for item in points_list if item[1] != 0.0 or item[2] != 0]
    
    auto_msg = ""
    if len(non_zero_items) == 2:
        entered_idxs = [item[0] for item in non_zero_items]
        target_idx = [i for i in [1, 2, 3] if i not in entered_idxs][0]
        
        other_idxs = entered_idxs
        calc_pt = - (st.session_state[f"p{other_idxs[0]}_p_{date_str}_{game_idx}"] + st.session_state[f"p{other_idxs[1]}_p_{date_str}_{game_idx}"])
        calc_chip = - (st.session_state[f"p{other_idxs[0]}_c_{date_str}_{game_idx}"] + st.session_state[f"p{other_idxs[1]}_c_{date_str}_{game_idx}"])
        
        target_name = p1_name if target_idx == 1 else (p2_name if target_idx == 2 else p3_name)
        
        # ウィジェット描画前なので安全にセッションを書き換えられる
        st.session_state[f"p{target_idx}_p_{date_str}_{game_idx}"] = calc_pt
        st.session_state[f"p{target_idx}_c_{date_str}_{game_idx}"] = calc_chip
        
        auto_msg = f"✨ **{target_name}** の数値を自動計算しました（ゲームPt: {calc_pt:+.1f} / チップ: {calc_chip:+d}枚）"

    if auto_msg:
        st.info(auto_msg)

    # 入力フォームの描画
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        st.markdown(f"**{p1_name}**")
        p1_pt = st.number_input("ゲームPt", step=1.0, key=f"p1_p_{date_str}_{game_idx}")
        p1_chip = st.number_input("チップ枚数", step=1, key=f"p1_c_{date_str}_{game_idx}")

    with col2:
        st.markdown(f"**{p2_name}**")
        p2_pt = st.number_input("ゲームPt", step=1.0, key=f"p2_p_{date_str}_{game_idx}")
        p2_chip = st.number_input("チップ枚数", step=1, key=f"p2_c_{date_str}_{game_idx}")

    with col3:
        st.markdown(f"**{p3_name}**")
        p3_pt = st.number_input("ゲームPt", step=1.0, key=f"p3_p_{date_str}_{game_idx}")
        p3_chip = st.number_input("チップ枚数", step=1, key=f"p3_c_{date_str}_{game_idx}")

    # 結果の追加ボタン
    if st.button("➕ この半荘の結果を記録する", type="primary", use_container_width=True):
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

    # 選択した日付の成績表示
    if current_history:
        st.markdown("---")
        st.subheader(f"📊 【{date_str}】の当日スコア")

        players_summary = {}
        for r in current_history:
            for p_idx in [1, 2, 3]:
                p_name = r[f"p{p_idx}_name"]
                if p_name not in players_summary:
                    players_summary[p_name] = {"game_pt": 0.0, "chip_count": 0}
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
                    value=f"{p['total_pt']:+.1f} pt",
                    delta=f"本日総合計",
                )
                st.caption(
                    f"🎮 **ゲームPt:** {p['game_pt']:+.1f} pt\n\n"
                    f"🪙 **チップPt:** {p['chip_pt']:+.1f} pt ({p['chip_count']}枚)"
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

        col_left, col_right = st.columns([1, 1])
        with col_left:
            if st.button("↩️ 最後の半荘を取り消す", use_container_width=True):
                current_history.pop()
                save_all_to_sheet(st.session_state.history_by_date)
                st.cache_data.clear()
                st.rerun()
        with col_right:
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
        for r in all_records:
            game_results = [
                (r["p1_name"], r["p1_pt"], r["p1_chip"]),
                (r["p2_name"], r["p2_pt"], r["p2_chip"]),
                (r["p3_name"], r["p3_pt"], r["p3_chip"]),
            ]
            game_results.sort(key=lambda x: x[1], reverse=True)

            for rank_idx, (name, g_pt, chip) in enumerate(game_results, start=1):
                if name not in stats:
                    stats[name] = {
                        "games": 0,
                        "total_game_pt": 0.0,
                        "total_chips": 0,
                        "r1_count": 0,
                        "r2_count": 0,
                        "r3_count": 0,
                    }
                stats[name]["games"] += 1
                stats[name]["total_game_pt"] += g_pt
                stats[name]["total_chips"] += chip
                if rank_idx == 1:
                    stats[name]["r1_count"] += 1
                elif rank_idx == 2:
                    stats[name]["r2_count"] += 1
                elif rank_idx == 3:
                    stats[name]["r3_count"] += 1

        ranking_list = []
        for name, s in stats.items():
            chip_pt = s["total_chips"] * chip_rate
            total_pt = s["total_game_pt"] + chip_pt
            avg_rank = (
                (s["r1_count"] * 1 + s["r2_count"] * 2 + s["r3_count"] * 3) / s["games"]
                if s["games"] > 0
                else 0.0
            )

            ranking_list.append({
                "プレイヤー名": name,
                "通算総合Pt": round(total_pt, 1),
                "ゲームPt": round(s["total_game_pt"], 1),
                "チップPt": round(chip_pt, 1),
                "対局数": s["games"],
                "1着数": s["r1_count"],
                "2着数": s["r2_count"],
                "3着数": s["r3_count"],
                "平均順位": round(avg_rank, 2),
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
