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
        
        # 数値データの型変換（Ptとチップを数値に直す）
        for col in ["P1_Pt", "P1_チップ", "P2_Pt", "P2_チップ", "P3_Pt", "P3_チップ"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="fillna").fillna(0.0)
                
        return df.dropna(how="all")
    except Exception as e:
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        return pd.DataFrame(columns=columns)

# 3. データをスプレッドシートに保存する関数
def save_data(df):
    client = get_gspread_client()
    sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
    sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
    
    columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
    sheet.clear()
    sheet.append_row(columns)
    for _, row in df.iterrows():
        sheet.append_row([str(val) for val in row.tolist()])


# ==========================================
# 画面の実行部分
# ==========================================

st.title("🀄 サンマ（3人麻雀）スコア＆チップ計算")

# データのロード
df = load_data()

# 自動で「〇回戦」の数値を計算
next_match_num = len(df) + 1
default_match_text = f"{next_match_num}回戦"

# サイドバー：対局結果の入力
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
    new_row = pd.DataFrame([{
        "日付": str(match_date),
        "半荘": match_count,
        "P1名": p1_name, "P1_Pt": float(p1_pt_val), "P1_チップ": int(p1_chip_val),
        "P2名": p2_name, "P2_Pt": float(p2_pt_val), "P2_チップ": int(p2_chip_val),
        "P3名": p3_name, "P3_Pt": float(p3_pt_val), "P3_チップ": int(p3_chip_val),
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    
    st.sidebar.success("スプレッドシートに保存しました！")
    st.rerun()

# ==========================================
# メイン画面：総合成績の集計＆履歴表示
# ==========================================

if not df.empty:
    # プレイヤーごとの集計処理
    summary_data = []
    # データフレームからすべてのプレイヤー名を集める
    all_players = set()
    for i in range(1, 4):
        all_players.update(df[f"P{i}name"].dropna().unique())
        
    for player in all_players:
        if not player or player.strip() == "":
            continue
        total_pt = 0.0
        total_chip = 0
        matches_played = 0
        
        for _, row in df.iterrows():
            for i in range(1, 4):
                if row.get(f"P{i}name") == player:
                    total_pt += float(row.get(f"P{i}_Pt", 0))
                    total_chip += int(row.get(f"P{i}_チップ", 0))
                    matches_played += 1
                    
        summary_data.append({
            "プレイヤー名": player,
            "半荘数": matches_played,
            "トータルPt": round(total_pt, 1),
            "トータルチップ": total_chip
        })
        
    if summary_data:
        st.header("🏆 総合成績サマリー")
        summary_df = pd.DataFrame(summary_data)
        # ポイント順に並び替え
        summary_df = summary_df.sort_values(by="トータルPt", ascending=False).reset_index(drop=True)
        st.dataframe(summary_df, use_container_width=True)

    st.header("📊 対局履歴一覧")
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    if st.button("全データをリセット（注意）"):
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        empty_df = pd.DataFrame(columns=columns)
        save_data(empty_df)
        st.success("データをリセットしました。")
        st.rerun()
else:
    st.info("まだ対局データがありません。サイドバーからデータを入力してください！")
