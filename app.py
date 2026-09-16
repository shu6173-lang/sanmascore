import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread

# ページの設定
st.set_page_config(
    page_title="サンマ（3人麻雀）スコア＆チップ計算",
    page_icon="🀄",
    layout="centered"
)

# 1. Googleスプレッドシートに接続する関数
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

# 2. スプレッドシートからデータを読み込む関数
@st.cache_data(ttl=0)
def load_data():
    try:
        client = get_gspread_client()
        sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
        sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
        data = sheet.get_all_values()
        
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        
        if not data or len(data) <= 1:
            return pd.DataFrame(columns=columns)
            
        df = pd.DataFrame(data[1:], columns=columns[:len(data[0])])
        return df.dropna(how="all")
    except Exception as e:
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        return pd.DataFrame(columns=columns)

# 3. データをスプレッドシートに追記する関数
def append_data(row_list):
    client = get_gspread_client()
    sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
    sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
    sheet.append_row(row_list)

# 4. データを全リセットする関数
def reset_data():
    client = get_gspread_client()
    sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
    sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
    columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
    sheet.clear()
    sheet.append_row(columns)


# ==========================================
# 画面の実行部分
# ==========================================

st.title("🀄 サンマ（3人麻雀）スコア＆チップ計算")

# データのロード
df = load_data()

# 自動で「〇回戦」の数値を計算
next_match_num = len(df) + 1
default_match_text = f"{next_match_num}回戦"

# ==========================================
# サイドバー：日付選択メニュー ＆ 対局結果の入力
# ==========================================
st.sidebar.header("📅 過去の記録フィルター")

selected_date_filter = "すべて表示"
if not df.empty and "日付" in df.columns:
    # 記録されている日付の一覧を取得（重複なし、新しい順など）
    recorded_dates = sorted(df["日付"].dropna().unique(), reverse=True)
    date_options = ["すべて表示"] + list(recorded_dates)
    selected_date_filter = st.sidebar.selectbox("表示する日付を選択", date_options)

st.sidebar.markdown("---")
st.sidebar.header("📝 対局結果の入力")

with st.sidebar.form("score_form"):
    match_date = st.date_input("対局日")
    match_count = st.text_input("半荘", default_match_text)
    
    st.subheader("プレイヤー1")
    p1_name = st.text_input("名前 (1)", "プレイヤーA")
    p1_pt_val = st.number_input("ポイント (1) [例: +15, -10]", value=0.0, step=1.0, format="%.1f")
    p1_chip_val = st.number_input("チップ数 (1)", value=0, step=1)

    st.subheader("プレイヤー2")
    p2_name = st.text_input("名前 (2)", "プレイヤーB")
    p2_pt_val = st.number_input("ポイント (2) [例: +5, -5]", value=0.0, step=1.0, format="%.1f")
    p2_chip_val = st.number_input("チップ数 (2)", value=0, step=1)

    st.subheader("プレイヤー3")
    p3_name = st.text_input("名前 (3)", "プレイヤーC")
    p3_pt_val = st.number_input("ポイント (3) [例: -20, +10]", value=0.0, step=1.0, format="%.1f")
    p3_chip_val = st.number_input("チップ数 (3)", value=0, step=1)

    submitted = st.form_submit_button("計算して記録する")

if submitted:
    row_data = [
        str(match_date), match_count,
        p1_name, str(p1_pt_val), str(p1_chip_val),
        p2_name, str(p2_pt_val), str(p2_chip_val),
        p3_name, str(p3_pt_val), str(p3_chip_val)
    ]
    append_data(row_data)
    st.cache_data.clear()
    st.sidebar.success("スプレッドシートに保存しました！")
    st.rerun()

# ==========================================
# メイン画面：総合成績の集計＆履歴表示
# ==========================================

if not df.empty:
    # 選択された日付で絞り込み（「すべて表示」でなければその日付のデータだけにする）
    display_df = df.copy()
    if selected_date_filter != "すべて表示":
        display_df = display_df[display_df["日付"] == selected_date_filter]

    # プレイヤーごとの集計処理（※トータルは全期間、または絞り込み時に合算するかはお好みですが、全期間の総合を出すか選んだ日だけにすることも可能です。今回は全体の総合成績を表示しつつ、履歴を絞り込めるようにしています）
    summary_dict = {}
    
    for _, row in df.iterrows():
        players_in_row = [
            (row.get("P1名"), row.get("P1_Pt"), row.get("P1_チップ")),
            (row.get("P2名"), row.get("P2_Pt"), row.get("P2_チップ")),
            (row.get("P3名"), row.get("P3_Pt"), row.get("P3_チップ")),
        ]
        
        for name, pt, chip in players_in_row:
            if not name or str(name).strip() == "":
                continue
            name = str(name).strip()
            
            try:
                pt_val = float(pt) if pt != "" else 0.0
            except:
                pt_val = 0.0
                
            try:
                chip_val = int(float(chip)) if chip != "" else 0
            except:
                chip_val = 0
                
            if name not in summary_dict:
                summary_dict[name] = {"半荘数": 0, "トータルPt": 0.0, "トータルチップ": 0}
                
            summary_dict[name]["半荘数"] += 1
            summary_dict[name]["トータルPt"] += pt_val
            summary_dict[name]["トータルチップ"] += chip_val

    summary_data = []
    for name, stats in summary_dict.items():
        summary_data.append({
            "プレイヤー名": name,
            "半荘数": stats["半荘数"],
            "トータルPt": round(stats["トータルPt"], 1),
            "トータルチップ": stats["トータルチップ"]
        })
        
    if summary_data:
        st.header("🏆 総合成績サマリー（全期間）")
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values(by="トータルPt", ascending=False).reset_index(drop=True)
        st.dataframe(summary_df, use_container_width=True)

    # 履歴一覧（選択した日付でフィルターされたもの）
    if selected_date_filter == "すべて表示":
        st.header("📊 対局履歴一覧（すべて）")
    else:
        st.header(f"📊 対局履歴一覧 ({selected_date_filter})")
        
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    if st.button("全データをリセット（注意）"):
        reset_data()
        st.cache_data.clear()
        st.success("データをリセットしました。")
        st.rerun()
else:
    st.info("まだ対局データがありません。サイドバーからデータを入力してください！")
