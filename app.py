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

# 3. データをスプレッドシートに保存する関数
def save_data(df):
    client = get_gspread_client()
    sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
    sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
    
    columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
    sheet.clear()
    sheet.append_row(columns)
    for _, row in df.iterrows():
        sheet.append_row(row.tolist())


# ==========================================
# ここから下が画面の実行部分（関数定義の後ろに配置）
# ==========================================

# アプリのタイトル
st.title("🀄 サンマ（3人麻雀）スコア＆チップ計算")

# データのロード（関数が定義された後なので、ここで正しく呼び出せます）
df = load_data()

# 現在のデータ行数＋1を「何回戦目か」の自動初期値にする
next_match_num = len(df) + 1
default_match_text = f"{next_match_num}回戦"

# サイドバー：対局結果の入力
st.sidebar.header("📝 対局結果の入力")

with st.sidebar.form("score_form"):
    match_date = st.date_input("対局日")
    match_count = st.text_input("半荘", default_match_text)
    
    # 3人分のプレイヤー名とpt・チップの入力
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
        "P1名": p1_name, "P1_Pt": p1_pt_val, "P1_チップ": p1_chip_val,
        "P2名": p2_name, "P2_Pt": p2_pt_val, "P2_チップ": p2_chip_val,
        "P3名": p3_name, "P3_Pt": p3_pt_val, "P3_チップ": p3_chip_val,
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    
    st.sidebar.success("スプレッドシートに保存しました！")
    st.rerun()

# メイン画面：成績一覧
st.header("📊 対局履歴一覧")

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    if st.button("全データをリセット（注意）"):
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        empty_df = pd.DataFrame(columns=columns)
        save_data(empty_df)
        st.success("データをリセットしました。")
        st.rerun()
else:
    st.info("まだ対局データがありません。サイドバーからデータを入力してください！")
