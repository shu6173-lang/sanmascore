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

# Googleスプレッドシートに接続する関数
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

# スプレッドシートからデータを読み込む
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

# データをスプレッドシートに保存する
def save_data(df):
    client = get_gspread_client()
    sheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
    sheet = client.open_by_key(sheet_id).worksheet("Sheet1")
    
    columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
    sheet.clear()
    sheet.append_row(columns)
    for _, row in df.iterrows():
        sheet.append_row(row.tolist())

# アプリのタイトル
st.title("🀄 サンマ（3人麻雀）スコア＆チップ計算")

# データのロード
df = load_data()

# サイドバー：対局結果の入力
st.sidebar.header("📝 対局結果の入力")

with st.sidebar.form("score_form"):
    match_date = st.date_input("対局日")
    match_count = st.text_input("半荘（例: 1回戦）", "1回戦")
    
    # 3人分のプレイヤー名とスコア・チップの入力（初期値を35000点に変更）
    st.subheader("プレイヤー1")
    p1_name = st.text_input("名前 (1)", "プレイヤーA")
    p1_score = st.number_input("持ち点 (1)", value=35000, step=1000)
    p1_chip = st.number_input("チップ数 (1)", value=0, step=1)

    st.subheader("プレイヤー2")
    p2_name = st.text_input("名前 (2)", "プレイヤーB")
    p2_score = st.number_input("持ち点 (2)", value=35000, step=1000)
    p2_chip = st.number_input("チップ数 (2)", value=0, step=1)

    st.subheader("プレイヤー3")
    p3_name = st.text_input("名前 (3)", "プレイヤーC")
    p3_score = st.number_input("持ち点 (3)", value=35000, step=1000)
    p3_chip = st.number_input("チップ数 (3)", value=0, step=1)

    # 設定（レートやウマなど）
    st.subheader("⚙️ ルール設定")
    return_score = st.number_input("返し点（基準点）", value=40000, step=1000)
    uma_1 = st.number_input("ウマ 1位", value=20, step=5)
    uma_2 = st.number_input("ウマ 2位", value=0, step=5)
    uma_3 = st.number_input("ウマ 3位", value=-20, step=5)

    submitted = st.form_submit_button("計算して記録する")

if submitted:
    # スコアの計算（(持ち点 - 返し点) / 1000 + ウマ）
    p1_pt = ((p1_score - return_score) / 1000) + uma_1
    p2_pt = ((p2_score - return_score) / 1000) + uma_2
    p3_pt = ((p3_score - return_score) / 1000) + uma_3

    # 1行分のデータを作成
    new_row = pd.DataFrame([{
        "日付": str(match_date),
        "半荘": match_count,
        "P1名": p1_name, "P1_Pt": p1_pt, "P1_チップ": p1_chip,
        "P2名": p2_name, "P2_Pt": p2_pt, "P2_チップ": p2_chip,
        "P3名": p3_name, "P3_Pt": p3_pt, "P3_チップ": p3_chip,
    }])

    # 既存データに追加して保存
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
これで全員35000点スタートになります！
